import copy
from requests import sessions
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter

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
                    url: '/n1.0/fluttercomic/orders/callback/paypal/%(oid)d',
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


class PayPalApi(PlatFormClient):

    API = 'https://api.paypal.com'
    SANDBOXAPI = 'https://api.sandbox.paypal.com'

    def __init__(self, conf):
        super(PayPalApi, self).__init__(NAME, conf)

        self.auth = HTTPBasicAuth(username=conf.clientID, password=conf.secret)
        self.api = self.SANDBOXAPI if self.sandbox else self.API


    def html(self, **kwargs):
        _kwargs = copy.copy(kwargs)
        _kwargs.update({'env': 'sandbox' if self.sandbox else 'production'})
        buf = HTMLTEMPLATE % _kwargs
        return encodeutils.safe_decode(buf, 'utf-8')

    def payment(self, money, cancel):
        money = '%.2f' % (money*self.roe)
        url = self.api + '/v1/payments/payment'
        data = dict(
            intent='sale',
            payer={'payment_method': 'paypal'},
            transactions=[dict(amount=dict(total=money, currency=self.currency))],
            redirect_urls={"return_url": "http://www.163.com",
                           "cancel_url": cancel}
        )
        resp = self.session.post(url, auth=self.auth, json=data,
                                 headers={"Content-Type": "application/json"},
                                 timeout=10)
        payment =  jsonutils.loads_as_bytes(resp.text)
        if payment.get('state') != 'created':
            raise exceptions.CreateOrderError('Create Paypal payment error')
        return payment['id']

    def _execute(self, paypal, money):
        money = '%.2f' % (money*self.roe)
        url = self.api + '/v1/payments/payment' + '/%s/execute' % paypal.get('paymentID')
        data = dict(payer_id=paypal.get('payerID'),
                    transactions=[dict(amount=dict(total=money, currency=self.currency))])
        resp = self.session.post(url, auth=self.auth, json=data,
                                 headers={"Content-Type": "application/json"}, timeout=10)
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(resp.text)
        return jsonutils.loads_as_bytes(resp.text)

    def execute(self, paypal, money):
        pay_result = self._execute(paypal, money)
        state = pay_result.get('state')
        if state is None or state == 'failed':
            LOG.error('Payment execute status fail')
            raise exceptions.EsureOrderError('Payment execute result is not success')
