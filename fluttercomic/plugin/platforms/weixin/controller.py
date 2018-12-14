# -*- coding:utf-8 -*-
import time
import webob
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

from fluttercomic import common
from fluttercomic.plugin.platforms.base import PlatformsRequestBase
from fluttercomic.plugin.platforms.weixin.client import WeiXinApi

from fluttercomic.models import Order
from fluttercomic.models import User
from fluttercomic.models import RechargeLog
from fluttercomic.models import DuplicateRecharge

from fluttercomic.api import endpoint_session

from fluttercomic.plugin.platforms.weixin import config
from fluttercomic.plugin.platforms import exceptions

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

CONF.register_group(config.group)
config.register_opts(config.group)
weiXinApi = WeiXinApi(CONF[config.group.name])

FAULT_MAP = {InvalidArgument: webob.exc.HTTPClientError,
             NoResultFound: webob.exc.HTTPNotFound,
             MultipleResultsFound: webob.exc.HTTPInternalServerError,
             exceptions.EsureOrderError: webob.exc.HTTPInternalServerError
             }


NEWPAYMENT = {
    'type': 'object',
    'required': ['money', 'uid', 'oid', 'url'],
    'properties':
        {
            'money': {'type': 'integer', 'minimum': 1},
            'uid': {'type': 'integer', 'minimum': 1},
            'cid': {'type': 'integer', 'minimum': 0},
            'chapter': {'type': 'integer', 'minimum': 0},
         }

}


ESUREPAY = {
    'type': 'object',
    'required': ['paypal', 'uid'],
    'properties':
        {
            'uid': {'type': 'integer', 'minimum': 1},
            'paypal': {
                'type': 'object',
                'required': ['paymentID', 'payerID'],
                'properties' : {
                    'paymentID': {'type': 'string', 'minLength': 5, 'maxLength': 128},
                    'payerID': {'type': 'string', 'minLength': 5, 'maxLength': 128},
                }
            },
         }
}


@singleton.singleton
class WeiXinRequest(PlatformsRequestBase):


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

        oid = uuidutils.Gkey()
        session = endpoint_session()
        prepay_id = weiXinApi.payment(money, oid, start_time, req)
        coins = self.order(session, weiXinApi, None,
                           uid, oid, money, cid, chapter,
                           ext={'prepay_id': prepay_id},
                           order_time=start_time)
        return resultutils.results(result='create paypal payment success',
                                   data=[dict(oid=oid, coins=coins, money=money,
                                              prepay_id=prepay_id)])

    def notify(self, req, oid, body=None):
        """这个接口由微信调用"""
        oid = int(oid)
        now = int(time.time()*1000)
        otime = uuidutils.Gprimarykey.timeformat(oid)
        if (now - otime) > weiXinApi.overtime*2 or otime > now:
            raise InvalidArgument('Order id error or overtime')
        session = endpoint_session()
        query = model_query(session, Order, filter=Order.oid == oid)
        order = query.one()
        serial, extdata = weiXinApi.esure_notify(body, order)
        self.record(session, order, serial, extdata)
        return webob.Response(request=req, status=200, content_type='application/xml',
                              body=weiXinApi.success)


    def esure(self, req, oid, body=None):
        """这个接口由客户端调用"""
        oid = int(oid)
        now = int(time.time()*1000)
        otime = uuidutils.Gprimarykey.timeformat(oid)
        if (now - otime) > weiXinApi.overtime*2 or otime > now:
            raise InvalidArgument('Order id error or overtime')

        session = endpoint_session(readonly=True)   # 注意主从不同步的可能
        query = model_query(session, RechargeLog, filter=RechargeLog.oid == oid)
        recharge = query.one_or_none()
        if recharge:
            return resultutils.results(result='esure orde success',
                                       data=[dict(oid=oid, coins=recharge.gift+recharge.coin, money=recharge.money)])
        session = endpoint_session()
        query = model_query(session, Order, filter=Order.oid == oid)
        order = query.one()
        serial, extdata = weiXinApi.esure_order(order)
        self.record(session, order, serial, extdata)
        return resultutils.results(result='esure orde success',
                                   data=[dict(oid=oid, coins=order.gift+order.coin, money=order.money)])

