from requests import sessions
from requests.auth import AuthBase
from requests.adapters import HTTPAdapter

from simpleutil.log import log as logging
from simpleutil.utils import jsonutils

LOG = logging.getLogger(__name__)

class HTTPBearerAuth(AuthBase):

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + self.token
        return r


class PayPalApi(object):


    PAYPALAPI = ''

    def __init__(self, conf):
        session = sessions.Session()
        session.mount('http', HTTPAdapter(pool_maxsize=25))
        session.mount('https', HTTPAdapter(pool_maxsize=25))
        # self.auth = HTTPBearerAuth(conf.token)
        self.auth = dict(username=conf.clientID, password=conf.secret)
        self.session = session

    def payment(self, money):
        url = self.PAYPALAPI + '/v1/payments/payment'
        data = dict(
            intent='sale',
            payer={'payment_method': 'paypal'},
            transactions=[
                dict(amount=dict(
                    total=money,
                    currency='USD'
                ))
            ]
        )
        resp = self.session.post(url, auth=self.auth, json=data, headers={"Content-Type": "application/json"},
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
