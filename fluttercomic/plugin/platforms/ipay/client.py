import copy
from collections import OrderedDict
from urllib import unquote
from urllib import urlencode

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import  InvalidSignature

from cryptography.hazmat.primitives.asymmetric import padding

from simpleutil.log import log as logging
from simpleutil.utils import jsonutils
from simpleutil.utils import encodeutils

from fluttercomic.plugin.platforms import exceptions
from fluttercomic.plugin.platforms.base import PlatFormClient
from fluttercomic.plugin.platforms.paypal.config import NAME

LOG = logging.getLogger(__name__)


HTMLTEMPLATE = '''
<script src="https://www.paypalobjects.com/api/checkout.js"></script>

<div id="paypal-button"></div>

<script>

    paypal.Button.render({
        style: {'label': 'buynow', 'size': 'responsive'},
        env: '%(env)s',
        payment: function (data, actions) {
            return actions.request({
                    method: "post",
                    url: '/n1.0/fluttercomic/orders/platforms/paypal',
                    json: {money: %(money)d, uid: %(uid)d, oid: '%(oid)d', cid: %(cid)d, chapter: %(chapter)d, url: '%(url)s'},
                })
                .then(function (res) {
                    return res.data[0].paypal.paymentID;
                });
        },
        onAuthorize: function (data, actions) {
            return actions.request({
                    method: "post",
                    url: '/n1.0/fluttercomic/orders/platforms/paypal/%(oid)d',
                    json: {paypal: { paymentID: data.paymentID, payerID: data.payerID}, uid: %(uid)d},
                })
                .then(function (res) {
                    window.postMessage(JSON.stringify({result: 'paypal pay success', success: true,
                    coins: res.data[0].coins, paypal: { paymentID: data.paymentID, payerID: data.payerID},
                    oid: %(oid)d}));
                });
        },
        onCancel: function(data, actions) {
            window.postMessage(JSON.stringify({success: false, result: 'paypal has been cancel'}));
        },
        onError: function (err) {
           window.postMessage(JSON.stringify({success: false, result: 'paypal catch error'}));
        }
    }, '#paypal-button');
</script>
'''


class IPayApi(PlatFormClient):

    ORDERURL = 'https://cp.iapppay.com/payapi/order'
    RESULTSURL = 'https://cp.iapppay.com/payapi'
    GWURL = 'https://web.iapppay.com/h5/gateway'

    TRANSDATA = 'transdata'

    HASHES = hashes.MD5

    # HASHES = hashes.SHA256
    # RASPRIVATEPADING = padding.PSS(mgf=padding.MGF1(HASHES()), salt_length=padding.PSS.MAX_LENGTH)

    RASPRIVATEPADING = padding.PKCS1v15()

    # RASPUBLICPADING = padding.PKCS1v15()
    RASPUBLICPADING = padding.OAEP(mgf=padding.MGF1(algorithm=HASHES()),
                                   algorithm=HASHES(),label=None)


    CURRENCYS = {'CNY': 'RMB'}

    def __init__(self, conf):
        super(IPayApi, self).__init__(NAME, conf)

        self.appid = conf.appId
        self.url_sucess = conf.url_sucess
        self.url_fail = conf.url_fail
        self.signtype = conf.signtype

        with open(conf.pem) as f:
            self.private_key = serialization.load_pem_private_key(data=f.read(),
                                                                  password=None,
                                                                  backend=default_backend())
        with open(conf.pem) as f:
            self.public_key = serialization.load_der_public_key(data=f.read(), backend=default_backend())

    @property
    def _currency(self):
        return IPayApi.CURRENCYS.get(self.currency, self.currency)


    def mksign(self, data, t):
        if t == 'RAS':
            try:
                return self.private_key.sign(data, IPayApi.RASPRIVATEPADING, IPayApi.HASHES())
            except Exception as e:
                LOG.error('Rsa sign error: %s' % e.__class__.__name__)
                raise exceptions.OrderError('ras sign fail')
        else:
            # TODO raise type error
            raise exceptions.OrderError('sign type error')

    def verify(self, data, sign, t):
        if t == 'RAS':
            try:
                self.public_key.verify(sign, data, IPayApi.RASPUBLICPADING, IPayApi.HASHES())
            except InvalidSignature:
                LOG.error('Rsa verify fail')
                return False
            except Exception as e:
                LOG.error('Rsa verify error: %s' % e.__class__.__name__)
                return False
            return True
        else:
            # TODO raise type error
            raise exceptions.OrderError('sign type error on verify')


    def ipay_url(self, transid):
        data = OrderedDict()
        data['tid'] = transid
        data['app'] = self.appid
        data['url_r'] = self.url_sucess
        data['url_h'] = self.url_fail

        return IPayApi.GWURL + '?' + urlencode(
            dict(
                data=jsonutils.dumps(data),
                sign=self.mksign(data, self.signtype),
                sign_type=self.signtype
            )
        )

    @staticmethod
    def decode(text, key):
        data = unquote(text).decode('utf8').split('&')
        ok = False if key else True
        results = OrderedDict()
        for r in data:
            k, v = r.split('=')
            if k == key:
                ok = True
            results[k] = v
        if not ok:
            # TODO raise not found
            exceptions.OrderError('url decode key not found')
        return results

    def payment(self, money, oid, uid, req):
        money = '%.2f' % (money*self.roe)
        url = self.ORDERURL

        data = OrderedDict()
        data['appid'] = self.appid
        data['waresid'] = self.appid
        data['waresname'] = 'comic'
        data['cporderid'] = str(oid)
        data['price'] = money
        data['currency'] = self._currency
        data['appuserid'] = uid
        data['notifyurl'] = req.path_url + '/%d' % oid

        transdata = jsonutils.dumps(data)
        sign = self.mksign(transdata, self.signtype)
        LOG.error('rsa sign' + sign)
        resp = self.session.post(url,
                                 params=dict(transdata=transdata, sign=sign, signtype=self.signtype),
                                 headers={"Content-Type": "application/json"},
                                 timeout=10)

        results = IPayApi.decode(resp.text, self.TRANSDATA)
        transdata =  jsonutils.loads_as_bytes(results.get(self.TRANSDATA))
        if transdata.get('code'):
            msg = transdata.get('errmsg')
            LOG.error('ipay create payment fail %s' % str(msg))
            raise exceptions.CreateOrderError('Create ipay payment error')
        transid = transdata.get('transid')
        sign = results.get('sign')
        signtype = results.get('signtype')
        if not self.verify(results.get(self.TRANSDATA), sign, signtype):
            # TODO verify fail
            raise exceptions.OrderError('ras verify fail')

        return transid, self.ipay_url(transid)
