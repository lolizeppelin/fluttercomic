# -*- coding:utf-8 -*-
import time
import abc
import six
from requests import sessions
from requests.adapters import HTTPAdapter

from simpleutil.config import cfg
from simpleutil.log import log as logging
from simpleutil.utils import singleton
from simpleutil.utils import jsonutils

from simpleservice.wsgi.middleware import MiddlewareContorller
from simpleservice.ormdb.exceptions import DBError
from simpleservice.ormdb.exceptions import DBDuplicateEntry
from simpleservice.ormdb.api import model_query

from goperation.manager.utils import resultutils

from fluttercomic import common
from fluttercomic.models import Order
from fluttercomic.models import User
from fluttercomic.models import RechargeLog
from fluttercomic.models import DuplicateRecharge

CONF = cfg.CONF


LOG = logging.getLogger(__name__)


@singleton.singleton
class PlatformsRequestPublic(MiddlewareContorller):

    __conf = CONF[common.NAME]

    ADMINAPI = False

    def platforms(self):
        return resultutils.results(result='get platforms success',
                                   data=self.__conf.platforms)


class PlatformsRequestBase(MiddlewareContorller):

    ADMINAPI = False
    JSON = False

    @staticmethod
    def extrouters(router, mapper, controller):
        """ext router"""

    def html(self, req, body=None):
        raise NotImplementedError

    def new(self, req, body=None):
        """发起订单"""
        raise NotImplementedError

    def esure(self, req, oid, body=None):
        raise NotImplementedError

    def notify(self, req, oid, body=None):
        raise NotImplementedError

    @staticmethod
    def order(session, client, serial,
              uid, oid, money, cid, chapter,
              ext=None, order_time=None):
        query = model_query(session, User, filter=User.uid == uid)
        coin, gift = client.translate(money)
        with session.begin():
            user = query.one()
            order = Order(oid=oid, uid=uid,
                          sandbox=client.sandbox,
                          currency=client.currency,
                          platform=client.name,
                          money=money,
                          serial=serial,
                          time=order_time or int(time.time()),
                          cid=cid,
                          chapter=chapter,
                          coins=user.coins,
                          gifts=user.gifts,
                          coin=coin,
                          gift=gift,
                          ext=jsonutils.dumps(ext) if ext else None)
            session.add(order)
        return coin + gift

    @staticmethod
    def record(session, order, serial, extdata,
               on_transaction_call=None):

        uid = order.uid
        query = session.query(User).filter(User.uid == uid).with_for_update()

        try:
            with session.begin():
                user = query.one()
                if on_transaction_call:
                    extdata = on_transaction_call(extdata)
                recharge = RechargeLog(
                    oid=order.oid,
                    sandbox=order.sandbox,
                    uid=uid,
                    coins=user.coins,
                    gifts=user.gifts,
                    coin=order.coin,
                    gift=order.gift,
                    money=order.money,
                    currency=order.currency,
                    platform=order.platform,
                    time=order.time,
                    ftime=int(time.time()),
                    cid=order.cid,
                    chapter=order.chapter,
                    serial=serial if serial else order.serial,
                    ext=jsonutils.dumps(extdata) if extdata else None,
                )
                user.coins += order.coin
                user.gifts += order.gift
                session.add(recharge)
        except DBDuplicateEntry:
            LOG.warning('Duplicate esure notify')
            d = DuplicateRecharge(oid=order.oid, uid=order.uid,
                                  coin=order.coin, gift=order.gift,
                                  money=order.money, currency=order.currency,
                                  time=int(time.time()), status=common.NOTCHCEK,
                                  serial=order.serial)
            try:
                session.add(d)
            except DBError:
                LOG.error('Recodr duplicate recharge order fail')


@six.add_metaclass(abc.ABCMeta)
class PlatFormClient(object):

    def __init__(self, name, conf):
        session = sessions.Session()
        session.mount('http', HTTPAdapter(pool_maxsize=25))
        session.mount('https', HTTPAdapter(pool_maxsize=25))
        self.session = session
        self.platform = name
        self.conf = conf
        self.roe = conf.roe
        self.scale = conf.scale
        self.currency = conf.currency
        self.choices = set(conf.choices)
        LOG.info('%s roe is %f' % (self.name, self.roe))

    @property
    def name(self):
        return self.platform

    @property
    def sandbox(self):
        return self.conf.sandbox

    def translate(self, money):
        if money not in self.choices:
            LOG.warning('money number not in chioces')
        return (0, money*self.scale) if self.sandbox else (money*self.scale, 0)
