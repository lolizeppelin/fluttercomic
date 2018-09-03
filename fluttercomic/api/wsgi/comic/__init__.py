# -*- coding:utf-8 -*-
import time
import random
import string
import webob.exc
import msgpack



from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound
from simpleservice.ormdb.exceptions import DBDuplicateEntry

from simpleutil.log import log as logging
from simpleutil.utils import argutils
from simpleutil.utils import jsonutils
from simpleutil.utils import singleton

from simpleutil.common.exceptions import InvalidArgument

from simpleservice.ormdb.api import model_query
from simpleservice.wsgi.middleware import MiddlewareContorller
from simpleservice.ormdb.api import model_count_with_key


from goperation.manager import common as manager_common
from goperation.manager.utils import resultutils


from fluttercomic import common
from fluttercomic.models import User
from fluttercomic.models import UserOwn
from fluttercomic.models import UserBook
from fluttercomic.models import UserPayLog
from fluttercomic.models import Comic
from fluttercomic.models import Order
from fluttercomic.api import endpoint_session
from fluttercomic.api.wsgi.token import verify
from fluttercomic.api.wsgi.token import find_user
from fluttercomic.api.wsgi.utils import format_chapters


LOG = logging.getLogger(__name__)

FAULT_MAP = {InvalidArgument: webob.exc.HTTPClientError,
             NoResultFound: webob.exc.HTTPNotFound,
             MultipleResultsFound: webob.exc.HTTPInternalServerError}


Idformater = argutils.Idformater(key='request_id', formatfunc='request_id_check')


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
class ComicRequest(MiddlewareContorller):

    ADMINAPI = False

    def index(self, req, body=None):
        """列出漫画"""
        session = endpoint_session(readonly=True)
        query = model_query(session, Comic)
        return resultutils.results(result='show comic success',
                                   data=[dict(cid=comic.cid,
                                              name=comic.name,
                                              author=comic.author,
                                              type=comic.type,
                                              last=comic.last,
                                              lastup=comic.lastup)
                                         for comic in query])
    @verify(manager=True)
    def create(self, req, body=None):
        """创建新漫画"""
        body = body or {}

        name = body.get('name')
        type = body.get('type')
        region = body.get('region')
        author = body.get('author')
        session = endpoint_session()
        comic = Comic(name=name, type=type, author=author, region=region)
        session.add(comic)
        session.flush()
        return resultutils.results(result='create comic success', data=[dict(cid=comic.cid, name=comic.name)])

    def show(self, req, cid, body=None):
        """显示漫画详细, 自动确认用户是否登陆"""
        session = endpoint_session(readonly=True)
        query = model_query(session, Comic, filter=Comic.cid == cid)
        comic = query.one()
        if comic.status < 0:
            raise
        chapters = None
        uid = find_user(req)
        if uid:
            query = model_query(session, UserOwn.chapters, filter=and_(UserOwn.uid == uid, UserOwn.cid == cid))
            owns = query.one()
            chapters = owns.chapters
        elif comic.status == common.HIDE:
            raise
        return resultutils.results(result='show comic success',
                                   data=[dict(cid=comic.cid,
                                              name=comic.name,
                                              author=comic.author,
                                              type=comic.type,
                                              point=comic.point,
                                              chapters=format_chapters(comic.point, comic.chapters, chapters))])

    @verify(manager=True)
    def update(self, req, cid, body=None):
        pass

    @verify(manager=True)
    def delete(self, req, cid, body=None):
        pass

    @verify(manager=False)
    def buy(self, req, cid, chapter, uid, body=None):
        """购买一个章节"""
        body = body or {}
        uid = find_user(req)
        session = endpoint_session()
        query = model_query(session, Comic, filter=Comic.cid == cid)
        uquery = session.query(User).filter(User.uid == uid).with_for_update(nowait=True)
        oquery = model_query(session, UserOwn, filter=and_(UserOwn.uid == uid, UserOwn.cid == cid))
        comic = query.one()
        with session.begin():
            if comic.point >= chapter:
                raise
            if comic.last < chapter:
                raise
            user = uquery.one()

            coins = coin = user.coins
            gifts = gift = user.gifts
            if coin + gift < common.ONECHAPTER:
                raise
            # coins 不足
            if coin < common.ONECHAPTER:
                gift = common.ONECHAPTER - coin
            else:
                gift = 0
                coin = common.ONECHAPTER

            paylog = UserPayLog(uid=uid, cid=cid, chapter=chapter,
                                value=common.ONECHAPTER,
                                coin=coin, gift=gift,
                                coins=coins, gifts=gifts,
                                time=int(time.time()))
            session.add(paylog)
            session.flush()
            user.coins = coins - coin
            user.gifts = gifts - gift
            owns = oquery.one_or_none()
            if not owns:
                owns = UserOwn(uid=uid, cid=cid, chapters=msgpack.packb([chapter, ]))
                session.add(owns)
                session.flush()
            else:
                chapters = msgpack.unpackb(owns.chapters)
                chapters.append(chapter)
                owns.chapters = msgpack.packb(chapters)
                session.flush()

        return resultutils.results(result='buy chapter success',
                                   data=[dict(cid=comic.cid,
                                              name=comic.name,
                                              author=comic.author,
                                              type=comic.type,
                                              chapters=format_chapters(comic.point,
                                                                       comic.chapters,
                                                                       owns.chapters))])

    @verify(manager=False)
    def mark(self, req, cid, uid, body=None):
        """收藏漫画"""
        session = endpoint_session()
        if model_count_with_key(session, User, filter=UserBook.uid == uid) >= common.MAXBOOKS:
            raise
        query = model_query(session, Comic.name, filter=Comic.cid == cid)
        comic = query.one()
        try:
            session.add(UserBook(uid=uid, cid=cid, name=comic.name, time=int(time.time())))
            session.flush()
        except DBDuplicateEntry:
            LOG.warning('User alreday mark comic')
        return resultutils.results(result='mark book success',
                                   data=[dict(cid=comic.cid, name=comic.name)])

    @verify(manager=False)
    def unmark(self, req, cid, uid, body=None):
        """取消收藏"""
        session = endpoint_session()
        query = model_query(session, UserBook, filter=and_(User.uid == uid, UserBook.cid == cid))
        book = query.one_or_none()
        if book:
            query.delete(book)
            session.flush()
        return resultutils.results(result='unmark book success')

    @verify(manager=True)
    def new(self, req, cid, chapter, body=None):
        """添加新章节"""
        body = body or {}
        source = body.get('source')
        session = endpoint_session()
        query = session.query(User).filter(Comic.cid == cid).with_for_update()
        with session.begin():
            comic = query.one()
            last = comic.last
            if (last +1) != chapter:
                raise
            chapters = msgpack.unpackb(comic.chapters)
            if len(chapters) != comic.last:
                LOG.error('Comic chapters is uploading')
                raise
            comic.last = chapter
            session.flush()
            # 创建资源url加密key
            key = ''.join(random.sample(string.lowercase, 6))
            # TODO 启动一个websocket进程用于获取资源
            if source == 'local':
                host = None,
                port = None
                token = ''
            else:
                host = port = token = None
        return resultutils.results(result='finished update new chapter', data=[dict(cid=comic.cid,
                                                                                    name=comic.name,
                                                                                    token=token,
                                                                                    host=host, port=port)])
    @verify(manager=True)
    def finished(self, req, cid, chapter, body=None):
        """章节上传完成 通知开放"""
        body = body or {}
        max = body.get('max')           # 章节最大页数
        key = body.get('key')           # 加密key
        session = endpoint_session()
        query = session.query(User).filter(Comic.cid == cid).with_for_update()
        with session.begin():
            comic = query.one()
            last = comic.last
            if last != chapter:
                raise
            chapters = msgpack.unpackb(comic.chapters)
            if len(chapters) != (last - 1):
                LOG.error('Comic chapters is not uploading')
                raise
            chapters.append([max, key])
            comic.lastup = int(time.time())
            comic.chapters = msgpack.packb(chapters)
            session.flush()
        return resultutils.results(result='finished comic success', data=[dict(cid=comic.cid, name=comic.name)])


    @verify(manager=True)
    def unfinish(self, req, cid, chapter, body=None):
        """章节上传完成 失败, 通知还原"""
        body = body or {}
        session = endpoint_session()
        query = session.query(User).filter(Comic.cid == cid).with_for_update()
        with session.begin():
            comic = query.one()
            last = comic.last
            if last != chapter:
                raise
            chapters = msgpack.unpackb(comic.chapters)
            if len(chapters) != (last - 1):
                LOG.error('Comic chapters is not uploading')
                raise
            comic.last = last - 1
            session.flush()
        return resultutils.results(result='unfinish comic success', data=[dict(cid=comic.cid, name=comic.name)])