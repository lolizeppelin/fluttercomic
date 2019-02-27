from collections import OrderedDict
from urllib import unquote
from urllib import urlencode
import simplejson

import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import  InvalidSignature
from cryptography.hazmat.primitives.asymmetric import padding

from simpleutil.log import log as logging
from simpleutil.utils import jsonutils
# from simpleutil.utils import encodeutils

from fluttercomic.plugin.platforms import exceptions
from fluttercomic.plugin.platforms.base import PlatFormClient
from fluttercomic.plugin.platforms.paypal.config import NAME

LOG = logging.getLogger(__name__)


class IPayApi(PlatFormClient):

    ORDERURL = 'https://cp.iapppay.com/payapi/order'
    RESULTSURL = 'https://cp.iapppay.com/payapi'
    GWURL = 'https://web.iapppay.com/h5/gateway'

    TRANSDATA = 'transdata'

    HASHES = hashes.MD5

    # HASHES = hashes.SHA256
    # RSAPRIVATEPADING = padding.PSS(mgf=padding.MGF1(HASHES()), salt_length=padding.PSS.MAX_LENGTH)

    RSAPRIVATEPADING = padding.PKCS1v15()

    # RSAPUBLICPADING = padding.PKCS1v15()
    RSAPUBLICPADING = padding.OAEP(mgf=padding.MGF1(algorithm=HASHES()),
                                   algorithm=HASHES(),label=None)


    CURRENCYS = {'CNY': 'RMB'}

    def __init__(self, conf):
        super(IPayApi, self).__init__(NAME, conf)

        self.appid = conf.appId
        self.appuid = conf.appUid
        self.waresid = conf.waresId
        self.url_sucess = conf.url_sucess
        self.url_fail = conf.url_fail
        self.signtype = conf.signtype

        with open(conf.rsa_private) as f:
            self.private_key = serialization.load_pem_private_key(data=f.read(),
                                                                  password=None,
                                                                  backend=default_backend())
        with open(conf.rsa_public) as f:
            self.public_key = serialization.load_pem_public_key(data=f.read(),
                                                                backend=default_backend())
    @property
    def _currency(self):
        return IPayApi.CURRENCYS.get(self.currency, self.currency)

    def mksign(self, data, t):
        if t == 'RSA':
            try:
                sign = self.private_key.sign(data, IPayApi.RSAPRIVATEPADING, IPayApi.HASHES())
                return base64.b64encode(sign)
            except Exception as e:
                LOG.exception('Rsa sign error: %s' % e.__class__.__name__)
                raise exceptions.OrderError('RSA sign fail')
        else:
            # TODO raise type error
            raise exceptions.OrderError('sign type error')

    def verify(self, data, sign, t):
        if t == 'RSA':
            try:
                self.public_key.verify(base64.b64decode(sign), data,
                                       IPayApi.RSAPUBLICPADING, IPayApi.HASHES())
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
        data = jsonutils.dumps_as_bytes(data)
        return IPayApi.GWURL + '?' + urlencode(
            dict(
                data=data,
                sign=self.mksign(data, self.signtype),
                sign_type=self.signtype
            )
        )

    @staticmethod
    def decode(text, key):
        data = unquote(text.encode('utf-8')).split('&')
        ok = False if key else True
        results = OrderedDict()
        for r in data:
            for i, s in enumerate(r):
                if s == '=':
                    k = r[0:i]
                    v = r[i+1:]
                    break
            else:
                raise exceptions.OrderError('Can not split url data')
            if k == key:
                ok = True
            results[k] = v
        if not ok:
            # TODO raise not found
            exceptions.OrderError('url decode key not found')
        return results

    def payment(self, money, oid, req):
        money = round(money*self.roe, 2)

        data = OrderedDict()
        data['appid'] = self.appid
        data['waresid'] = self.waresid
        # data['waresname'] = 'comic'
        data['cporderid'] = str(oid)
        data['price'] = money
        data['currency'] = self._currency
        data['appuserid'] = self.appuid
        data['notifyurl'] = req.path_url + '/%d' % oid

        transdata = jsonutils.dumps_as_bytes(data)
        sign = self.mksign(transdata, self.signtype)
        LOG.debug('transdata is %s' % transdata)

        params=OrderedDict(transdata=transdata)
        params['sign'] = sign
        params['signtype'] = self.signtype

        resp = self.session.post(self.ORDERURL, data=urlencode(params), timeout=10)
        LOG.debug('response text ' % resp.text)
        results = IPayApi.decode(resp.text, self.TRANSDATA)
        transdata =  jsonutils.loads_as_bytes(results.get(self.TRANSDATA))
        if transdata.get('code'):
            LOG.error('ipay create payment fail %s, code %s' % (transdata.get('errmsg'),
                                                                str(transdata.get('code'))))
            raise exceptions.CreateOrderError('Create ipay payment error')
        LOG.debug('Create new payment success')
        transid = transdata.get('transid')
        sign = results.get('sign')
        signtype = results.get('signtype')
        if not self.verify(results.get(self.TRANSDATA), sign, signtype):
            # TODO verify fail
            raise exceptions.OrderError('RSA verify fail')

        return transid, self.ipay_url(transid)
