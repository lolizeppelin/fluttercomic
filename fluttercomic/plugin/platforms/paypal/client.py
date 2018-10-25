from requests import sessions
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter

from simpleutil.log import log as logging
from simpleutil.utils import jsonutils

LOG = logging.getLogger(__name__)

class PayPalApi(object):


    PAYPALAPI = 'https://api.sandbox.paypal.com'

    def __init__(self, conf):
        session = sessions.Session()
        session.mount('http', HTTPAdapter(pool_maxsize=25))
        session.mount('https', HTTPAdapter(pool_maxsize=25))
        self.auth = HTTPBasicAuth(username=conf.clientID, password=conf.secret)
        # self.auth = dict(username=conf.clientID, password=conf.secret)
        self.session = session
        self.conf = conf

    def payment(self, money):

        LOG.info('client id %s' % self.conf.clientID)
        LOG.info('secret %s' % self.conf.secret)

        url = self.PAYPALAPI + '/v1/payments/payment'
        data = dict(
            intent='sale',
            payer={'payment_method': 'paypal'},
            transactions=[dict(amount=dict(total=money, currency='USD'))],
            redirect_urls={"return_url": "http://www.163.com",
                           "cancel_url": "https://www.baidu.com"}
        )
        resp = self.session.post(url, auth=self.auth, json=data,
                                 headers={"Content-Type": "application/json"},
                                 timeout=10)
        LOG.info(resp.text)
        return jsonutils.loads_as_bytes(resp.text)

    def execute(self, paypal, money):
        url = self.PAYPALAPI + '/v1/payments/payment' + '/%s/execute ' % paypal.get('paymentID')
        data = dict(payer_id=paypal.get('payerID'))
        resp = self.session.post(url, auth=self.auth, json=data, headers={"Content-Type": "application/json"},
                                 timeout=10)
        LOG.info(resp.text)
        return jsonutils.loads_as_bytes(resp.text)
