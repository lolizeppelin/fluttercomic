# -*- coding:utf-8 -*-
import time
import webob.exc
from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

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
from fluttercomic.plugin.platforms.paypal.client import PayPalApi

from fluttercomic.models import Order
from fluttercomic.models import User
from fluttercomic.models import RechargeLog

from fluttercomic.api import endpoint_session

from fluttercomic.plugin.platforms.paypal import config

CONF = cfg.CONF
CONF.register_group(config.group)
CONF.register_opts(config.paypal_opts, config.group)

LOG = logging.getLogger(__name__)

paypalApi = PayPalApi(CONF[config.NAME])

FAULT_MAP = {InvalidArgument: webob.exc.HTTPClientError,
             NoResultFound: webob.exc.HTTPNotFound,
             MultipleResultsFound: webob.exc.HTTPInternalServerError}


NEWPAYMENT = {
    'type': 'object',
    'required': ['money', 'uid', 'oid', 'url'],
    'properties':
        {
            'money': {'type': 'integer', 'minimum': 1},
            'uid': {'type': 'integer', 'minimum': 1},
            'oid': {'type': 'string',
                    'minLength': 19, 'maxLength': 19,
                    'pattern': '^[^0]\d+$'
                    },
            'cid': {'type': 'integer', 'minimum': 0},
            'chapter': {'type': 'integer', 'minimum': 0},
            'url': {'type': 'string', 'format': 'uri', 'pattern': "^(https?|wss?|ftp)://"},
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
class PaypalRequest(PlatformsRequestBase):

    ADMINAPI = False
    JSON = False

    def html(self, req, body=None):
        """生成订单页面html"""
        try:
            money = int(req.params.get('money'))
            uid = int(req.params.get('uid'))
            cid = int(req.params.get('cid') or 0)
            chapter = int(req.params.get('chapter') or 0)
        except (ValueError, TypeError):
            LOG.debug(str(req.params))
            raise InvalidArgument('Some Value not int')

        if money < 1:
            raise InvalidArgument('Money less then 1')
        if uid < 1:
            raise InvalidArgument('Uid error')
        if cid < 0 or chapter < 0:
            raise InvalidArgument('cid or chapter less then 0')
        url = req.url
        oid = uuidutils.Gkey()
        return paypalApi.html(oid=oid, uid=uid, cid=cid, chapter=chapter, money=money, url=url)

    def new(self, req, body=None):
        """发起订单"""
        body = body or {}
        if not isinstance(body, dict):
            raise InvalidArgument('Http body not json or content type is not application/json')
        jsonutils.schema_validate(body, NEWPAYMENT)
        money = body.get('money')
        uid = body.get('uid')
        oid = int(body.get('oid'))
        cid = body.get('cid')
        chapter = body.get('chapter')
        cancel_url = body.get('url')

        now = int(time.time()*1000)
        otime = uuidutils.Gprimarykey.timeformat(oid)
        if (now - otime) > 60000 or otime > now:
            raise InvalidArgument('Order id error')

        coin, gift = paypalApi.translate(money)
        session = endpoint_session()
        query = model_query(session, User, filter=User.uid == uid)
        with session.begin():
            user = query.one()
            payment = paypalApi.payment(money, cancel_url)
            if payment.get('state') != 'created':
                raise InvalidArgument('Create order fail, call create payment error')
            order = Order(oid=oid, uid=uid,
                          sandbox=paypalApi.sandbox,
                          money=money,
                          platform='paypal',
                          serial=payment.get('id'),
                          time=int(time.time()),
                          cid=cid,
                          chapter=chapter,
                          coins=user.coins,
                          gifts=user.gifts,
                          coin=coin,
                          gift=gift)
            session.add(order)
        return resultutils.results(result='create paypal payment success',
                                   data=[dict(paypal=dict(paymentID=payment.get('id')),
                                              oid=oid, coins=coin+gift, money=money)
                                         ])

    def esure(self, req, oid, body=None):
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
        uquery = session.query(User).filter(User.uid == uid).with_for_update()

        with session.begin():
            order = query.one()
            if order.uid != uid:
                raise InvalidArgument('User id not the same')
            if order.serial != paypal.get('paymentID'):
                raise InvalidArgument('paymentID not the same')
            user = uquery.one()
            pay_result = paypalApi.execute(paypal, order.money)
            state = pay_result.get('state')
            if state is None or state == 'failed':
                raise InvalidArgument('Payment execute')

            recharge = RechargeLog(
                oid=order.oid,
                uid=uid,
                coins=user.coins,
                gifts=user.gifts,
                coin=order.coin,
                gift=order.gift,
                money=order.money,
                platform=order.platform,
                time=int(time.time()),
                cid=order.cid,
                chapter=order.chapter,
                sandbox=paypalApi.sandbox,
                ext=None,
            )
            user.coins += order.coin
            user.gifts += order.gift
            try:
                session.add(recharge)
            except Exception:
                LOG.error('Add recharge fail, order id %d' % order.oid)

        return resultutils.results(result='esure  orde success',
                                   data=[dict(paypal=dict(paymentID=paypal.get('paymentID'),
                                                          payerID=paypal.get('payerID')),
                                              oid=oid, coins=order.gift+order.coin, money=order.money)
                                         ])
