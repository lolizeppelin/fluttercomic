# -*- coding:utf-8 -*-
import time
import webob.exc
from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound
from simpleservice.ormdb.exceptions import DBError
from simpleservice.ormdb.exceptions import DBDuplicateEntry

from simpleutil.log import log as logging
from simpleutil.config import cfg
from simpleutil.utils import argutils
from simpleutil.utils import singleton
from simpleutil.utils import uuidutils
from simpleutil.utils import jsonutils

from simpleutil.common.exceptions import InvalidArgument

from simpleservice.ormdb.api import model_query
from simpleservice.wsgi.middleware import MiddlewareContorller


from goperation import threadpool
from goperation.manager.utils import resultutils

from fluttercomic.api.wsgi.token import verify
from fluttercomic.plugin.platforms.base import PlatformsRequestBase
from fluttercomic.plugin.platforms.ipay.client import IPayApi

from fluttercomic.models import Order
from fluttercomic.models import User
from fluttercomic.models import RechargeLog

from fluttercomic.api import endpoint_session

from fluttercomic.plugin.platforms.ipay import config
from fluttercomic.plugin.platforms import exceptions

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

CONF.register_group(config.group)
config.register_opts(config.group)
iPayApi = IPayApi(CONF[config.group.name])

FAULT_MAP = {InvalidArgument: webob.exc.HTTPClientError,
             NoResultFound: webob.exc.HTTPNotFound,
             MultipleResultsFound: webob.exc.HTTPInternalServerError,
             exceptions.EsureOrderError: webob.exc.HTTPInternalServerError
             }


NEWPAYMENT = {
    'type': 'object',
    'required': ['money', 'uid'],
    'properties':
        {
            'money': {'type': 'integer', 'minimum': 1},
            'uid': {'type': 'integer', 'minimum': 1},
            'cid': {'type': 'integer', 'minimum': 0},
            'chapter': {'type': 'integer', 'minimum': 0},
            'h5': {'type': 'boolean', 'description': '是否h5方式支付'},
         }

}


ESUREPAY = {
    'type': 'object',
    'required': ['transtype', 'cporderid', 'transid',
                 'appuserid', 'appid', 'waresid',
                 'feetype', 'money','currency',
                 'result', 'transtime'],
    'properties':
        {
            'transtype': {'type': 'integer', 'minimum': 1},
            'cporderid': {'type': 'integer', 'minimum': 1},
            'transid': {'type': 'integer', 'minimum': 1},
            'appuserid': {'type': 'integer', 'minimum': 1},
            'appid': {'type': 'integer', 'minimum': 1},
            'waresid': {'type': 'integer', 'minimum': 1},
            'feetype': {'type': 'integer', 'minimum': 1},
            'money': {'type': 'integer', 'minimum': 1},
            'currency': {'type': 'integer', 'minimum': 1},
            'result': {'type': 'integer', 'minimum': 1},
            'transtime': {'type': 'integer', 'minimum': 1},
         }
}

@singleton.singleton
class IpayRequest(PlatformsRequestBase):


    def new(self, req, body=None):
        """发起订单"""
        body = body or {}
        if not isinstance(body, dict):
            raise InvalidArgument('Http body not json or content type is not application/json')
        jsonutils.schema_validate(body, NEWPAYMENT)
        money = body.get('money')
        uid = body.get('uid')
        cid = body.get('cid')
        chapter = body.get('chapter')
        start_time = int(time.time())

        LOG.error('money')

        oid = uuidutils.Gkey()
        transid, url = iPayApi.payment(money, oid, uid, req)

        session = endpoint_session()
        coins = self.order(session, IPayApi, transid,
                           uid, oid, money, cid, chapter,
                           order_time=start_time)

        return resultutils.results(result='create ipay payment success',
                                   data=[dict(ipay=dict(transid=transid, url=url),
                                              oid=oid, coins=coins, money=money)])

    def notify(self, req, oid, body=None):
        body = body or {}
        if not isinstance(body, dict):
            raise InvalidArgument('Http body not json or content type is not application/json')

        oid = int(oid)
        now = int(time.time()*1000)
        otime = uuidutils.Gprimarykey.timeformat(oid)
        if (now - otime) > 600000 or otime > now:
            raise InvalidArgument('Order id error or more the 600s')

        jsonutils.schema_validate(body, ESUREPAY)

        paypal = body.get('paypal')
        uid = body.get('uid')

        session = endpoint_session()
        query = model_query(session, Order, filter=Order.oid == oid)
        order = query.one()
        if order.uid != uid:
            raise InvalidArgument('User id not the same')
        if order.serial != paypal.get('paymentID'):
            raise InvalidArgument('paymentID not the same')
        try:
            self.record(session, order, None, None)
        except DBError:
            LOG.error('Ipay save order %d to database fail' % order.oid)
            raise

        return resultutils.results(result='notify orde success',
                                   data=[dict(paypal=dict(paymentID=paypal.get('paymentID'),
                                                          payerID=paypal.get('payerID')),
                                              oid=oid, coins=order.gift+order.coin, money=order.money)
                                         ])

    def esure(self, req, oid, body=None):
        raise NotImplementedError
