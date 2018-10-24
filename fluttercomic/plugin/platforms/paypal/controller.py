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

from simpleutil.common.exceptions import InvalidArgument

from simpleservice.ormdb.api import model_query
from simpleservice.wsgi.middleware import MiddlewareContorller


from goperation import threadpool
from goperation.manager.utils import resultutils

from fluttercomic.api.wsgi.token import verify
from fluttercomic.plugin.platforms.base import PlatformsRequestBase
from fluttercomic.plugin.platforms.paypal import template
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


@singleton.singleton
class PaypalRequest(PlatformsRequestBase):

    ADMINAPI = False

    def html(self, req, body=None):
        """生成订单页面html"""
        oid = uuidutils.Gkey()
        money = req.params.get('money')
        uid = req.params.get('uid')
        cid = req.params.get('cid') or 0
        chapter = body.get('chapter') or 0
        return template.html(oid, uid, cid, chapter, money)

    def new(self, req, body=None):
        """发起订单"""
        money = body.get('money')
        uid = body.get('uid')
        oid = body.get('oid')
        cid = body.get('cid')
        chapter = body.get('chapter')
        coin, gift = template.translate(money)
        session = endpoint_session()
        query = model_query(session, User, filter=User.uid == uid)
        with session.begin():
            user = query.one()
            payment = paypalApi.payment(money)
            if payment.get('state') != 'created':
                raise InvalidArgument('Create order fail')
            order = Order(oid=oid, uid=uid,
                          money=money,
                          platform='paypal',
                          serial=payment.get('paymentID'),
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
        paypal = body.get('paypal')
        oid = body.get('oid')
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
            if pay_result.get('state') == 'failed':
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
