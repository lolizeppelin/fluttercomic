# -*- coding:utf-8 -*-
import time
import random
import string
import msgpack
import webob.exc


from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound


from simpleutil.config import cfg
from simpleutil.log import log as logging
from simpleutil.utils import argutils
from simpleutil.utils import singleton
from simpleutil.utils import digestutils

from simpleutil.common.exceptions import InvalidArgument

from simpleservice.ormdb.api import model_query
from simpleservice.wsgi.middleware import MiddlewareContorller
from simpleservice.ormdb.exceptions import DBDuplicateEntry


from goperation import threadpool
from goperation.manager.exceptions import TokenError
from goperation.manager import common as manager_common
from goperation.manager.utils import resultutils
from goperation.manager.tokens import TokenProvider

from fluttercomic import common
from fluttercomic.models import User
from fluttercomic.models import UserBook
from fluttercomic.models import UserOwn
from fluttercomic.models import Comic
from fluttercomic.models import Order
from fluttercomic.models import UserPayLog
from fluttercomic.api import endpoint_session

from fluttercomic.api.wsgi.token import verify
from fluttercomic.api.wsgi.token import M
from fluttercomic.api.wsgi.token import B
from fluttercomic.plugin.platforms import Platforms


LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CF = CONF[common.NAME]


FAULT_MAP = {
    InvalidArgument: webob.exc.HTTPClientError,
    NoResultFound: webob.exc.HTTPNotFound,
    TokenError: webob.exc.HTTPUnauthorized,
    MultipleResultsFound: webob.exc.HTTPInternalServerError
}

INDEXSCHEMA = {
    'type': 'object',
    'properties':
        {
             'order': {'type': 'string'},                                     # short column name
             'desc': {'type': 'boolean'},                                     # reverse result
             'start': {'type': 'string', 'format': 'date-time'},              # request start time
             'end': {'type': 'string', 'format': 'date-time'},                # request end time
             'page_num': {'type': 'integer', 'minimum': 0},                   # pagen number
             'status': {'type': 'integer',                                    # filter status
                        'enum': [manager_common.ACTIVE, manager_common.UNACTIVE]},
         }
}


OVERTIMESCHEMA = {
     'type': 'object',
     'required': ['agent_time', 'agents'],
     'properties': {
             'agent_time': {'type': 'integer', 'minimum': 0},               # respone time
             'agents':  {'type': 'array', 'minItems': 1,                    # overtime agents list
                         'items': {'type': 'integer', 'minimum': 0}}
         }
}


@singleton.singleton
class UserRequest(MiddlewareContorller):

    ADMINAPI = False

    @verify(vtype=M)
    def index(self, req, body=None):
        session = endpoint_session(readonly=True)
        query = model_query(session, User)
        query = query.order_by(User.uid)
        return resultutils.results(result='list users success',
                                   data=[dict(name=user.name, uid=user.uid,
                                              coins=user.coins, gifts=user.gifts,
                                              status=user.status, regtime=user.regtime) for user in query])

    def create(self, req, body=None):
        """用户注册"""
        body = body or {}
        session = endpoint_session()
        name = body.get('name')
        passwd = body.get('passwd')
        salt = ''.join(random.sample(string.lowercase, 6))
        user = User(name=name, salt=salt, passwd=digestutils.strmd5(salt + passwd), regtime=int(time.time()))
        session.add(user)
        try:
            session.flush()
        except DBDuplicateEntry:
            return resultutils.results(result='user name duplicate', resultcode=manager_common.RESULT_ERROR)
        token = TokenProvider.create(req, dict(uid=user.uid, name=user.name), 3600)
        return resultutils.results(result='crate user success',
                                   data=[dict(token=token, uid=user.uid, name=user.name,
                                              coins=(user.coins + user.gifts),
                                              platforms=Platforms,
                                              one=max(0, CF.one - user.offer)
                                              )])

    @verify(vtype=M)
    def show(self, req, uid, body=None):
        """列出用户信息"""
        uid = int(uid)
        session = endpoint_session(readonly=True)
        query = model_query(session, User, filter=User.uid == uid)
        joins = joinedload(User.books, innerjoin=False)
        query = query.options(joins)
        user = query.one()
        return resultutils.results(result='show user success',
                                   data=[dict(name=user.name, uid=user.uid, offer=user.offer,
                                              coins=user.coins, gifts=user.gifts,
                                              status=user.status, regtime=user.regtime,
                                              books=[dict(cid=comic.cid, name=comic.name,
                                                          author=comic.author, time=comic.time)
                                                     for comic in user.books],
                                              owns=[dict(cid=own.cid, chapter=own.chapter)
                                                    for own in user.owns],
                                              )])

    @verify(vtype=M)
    def update(self, uid, body=None):
        raise NotImplementedError

    @verify(vtype=M)
    def delete(self, uid, body=None):
        raise NotImplementedError

    def login(self, req, uid, body=None):
        """用户登录"""
        body = body or {}
        passwd = body.get('passwd')
        session = endpoint_session(readonly=True)
        query = model_query(session, User, filter=User.name == uid)
        user = query.one()
        if not passwd:
            raise InvalidArgument('Need passwd')
        if user.passwd != digestutils.strmd5(user.salt + passwd):
            raise InvalidArgument('Password error')
        if not TokenProvider.is_fernet(req):
            raise InvalidArgument('Not supported for uuid token')
        token = TokenProvider.create(req, dict(uid=user.uid, name=user.name), 3600)
        return resultutils.results(result='login success',
                                   data=[dict(token=token,
                                              name=user.name,
                                              uid=user.uid,
                                              coins=(user.coins + user.gifts),
                                              platforms=Platforms,
                                              one=max(0, CF.one - user.offer)
                                              )])

    @verify()
    def coins(self, req, uid, body=None):
        """用户自查余额"""
        session = endpoint_session(readonly=True)
        query = model_query(session, User, filter=User.name == uid)
        user = query.one()
        return resultutils.results(result='login success',
                                   data=[dict(name=user.name,
                                              uid=user.uid,
                                              coins=(user.coins + user.gifts))])

    @verify()
    def books(self, req, uid, body=None):
        """列出收藏的漫画"""
        uid = int(uid)
        session = endpoint_session(readonly=True)
        query = model_query(session, UserBook, filter=UserBook.uid == uid)
        return resultutils.results(result='get book success',
                                   data=[dict(cid=book.cid, name=book.name, author=book.author, ext=book.ext)
                                         for book in query])

    @verify(vtype=B)
    def owns(self, req, uid, body=None):
        """列出已经购买的漫画"""
        uid = int(uid)
        session = endpoint_session(readonly=True)
        query = model_query(session, UserOwn, filter=UserOwn.uid == uid)
        return resultutils.results(result='get owns comics success',
                                   data=[dict(cid=own.cid, ext=own.ext, uid=own.uid,
                                              chapter=own.chapter)
                                         for own in query])

    @verify(vtype=M)
    def order(self, req, uid, body=None):
        """用户创建"""
        raise NotImplementedError('orders~~')

    @verify(vtype=M)
    def orders(self, req, uid, body=None):
        """用户订单列表"""
        raise NotImplementedError('orders~~')

    @verify(vtype=M)
    def paylogs(self, req, uid, body=None):
        """用户支付列表"""
        body = body or {}
        desc = body.get('desc', True)
        session = endpoint_session(readonly=True)
        query = model_query(session, UserPayLog)
        query = query.order_by(UserPayLog.time.desc() if desc else UserPayLog.time)
        return resultutils.results(result='list users paylogs success',
                                   data=[dict(cid=paylog.cid, chapter=paylog.chapter,
                                              value=paylog.value, offer=paylog.offer,
                                              coin=paylog.coin, gift=paylog.gift,
                                              coins=paylog.coins, gifts=paylog.gifts,
                                              time=paylog.time) for paylog in query])

    @verify(vtype=M)
    def gitf(self, req, uid, body=None):
        """后台发送gift接口"""
        raise NotImplementedError('gift~~')

