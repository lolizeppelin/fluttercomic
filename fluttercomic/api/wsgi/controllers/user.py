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
from simpleservice.ormdb.exceptions import DBDuplicateEntry

from simpleutil.log import log as logging
from simpleutil.utils import argutils
from simpleutil.utils import singleton
from simpleutil.utils import digestutils

from simpleutil.common.exceptions import InvalidArgument

from simpleservice.ormdb.api import model_query
from simpleservice.ormdb.api import model_count_with_key
from simpleservice.wsgi.middleware import MiddlewareContorller


from goperation import threadpool
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
from fluttercomic.api.wsgi.utils import format_chapters


LOG = logging.getLogger(__name__)

FAULT_MAP = {InvalidArgument: webob.exc.HTTPClientError,
             NoResultFound: webob.exc.HTTPNotFound,
             MultipleResultsFound: webob.exc.HTTPInternalServerError}


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

    @verify(manager=True)
    def index(self, req, body=None):
        raise NotImplementedError

    def create(self, req, body=None):
        """创建用户"""
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
                                   data=[dict(token=token, uid=user.uid, name=user.name)])

    @verify(manager=False)
    def show(self, req, uid, body=None):
        """列出用户信息"""
        session = endpoint_session(readonly=True)
        query = model_query(session, User, filter=User.uid == uid)
        user = query.one()
        query = model_query(session, UserBook, filter=UserBook.uid == uid)
        return resultutils.results(result='show user success',
                                   data=[dict(name=user.name, coins=user.coins,
                                              books=[dict(cid=book.cid, name=book.name)
                                                     for book in query])])

    @verify(manager=True)
    def update(self, uid, body=None):
        raise NotImplementedError

    @verify(manager=True)
    def delete(self, uid, body=None):
        raise NotImplementedError

    def login(self, req, uid, body=None):
        """用户登录"""
        body = body or {}
        passwd = body.get('passwd')
        session = endpoint_session(readonly=True)
        query = model_query(session, User, filter=User.uid == uid)
        user = query.one()
        if not passwd:
            raise InvalidArgument('Need passwd')
        if user.password != digestutils.strmd5(user.salt.encode('utf-8') + passwd):
            raise InvalidArgument('Password error')
        token = TokenProvider.create(req, dict(uid=uid, name=user.name), 3600)
        query = model_query(session, UserBook, filter=UserBook.uid == uid)
        return resultutils.results(result='login success',
                                   data=[dict(token=token, name=user.name, coins=user.coins,
                                              books=[dict(cid=book.cid, name=book.name)
                                                     for book in query])])

    @verify(manager=False)
    def books(self, req, uid, body=None):
        """列出收藏的漫画"""
        session = endpoint_session(readonly=True)
        query = model_query(session, UserBook, filter=UserBook.uid == uid)
        return resultutils.results(result='get book success',
                                   data=[dict(cid=book.cid, name=book.name) for book in query])

    @verify(manager=False)
    def order(self, req, uid, body=None):
        """创建充值订单"""
        body = body or {}
        coin = body.get('coin')
        money = coin * common.PROPORTION
        session = endpoint_session()
        query = model_query(session, User.coins, filter=User.uid == uid)
        user = query.one()
        if user.status != common.ACTIVE:
            raise
        order = Order(uid=uid, coins=user.coins, coin=coin, money=money,
                      platform=body.get('platform'), serial=body.get('serial'), time=int(time.time()),
                      cid=body.get('cid'), chapter=body.get('chapter'), ext=body.get('ext'))
        session.add(Order)
        session.flush()
        return resultutils.results(result='build order success',
                                   data=[dict(oid=order.oid, money=money)])

    @verify(manager=True)
    def gitf(self, req, uid, body=None):
        """后台发送gift接口"""