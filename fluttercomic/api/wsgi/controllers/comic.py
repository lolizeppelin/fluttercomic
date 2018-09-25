# -*- coding:utf-8 -*-
import os
import time
import random
import string
import webob.exc
import msgpack


import contextlib
import shutil

from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound
from simpleservice.ormdb.exceptions import DBDuplicateEntry

from simpleutil.config import cfg
from simpleutil.log import log as logging
from simpleutil.utils import argutils
from simpleutil.utils import jsonutils
from simpleutil.utils import singleton
from simpleutil.utils import zlibutils

from simpleutil.common.exceptions import InvalidArgument

from simpleservice.ormdb.api import model_query
from simpleservice.wsgi.middleware import MiddlewareContorller
from simpleservice.ormdb.api import model_count_with_key

from goperation.common import FILEINFOSCHEMA
from goperation.manager import common as manager_common
from goperation.manager.utils import resultutils
from goperation.websocket.launcher import LaunchRecverWebsocket

from fluttercomic import common
from fluttercomic.models import User
from fluttercomic.models import UserOwn
from fluttercomic.models import UserBook
from fluttercomic.models import UserPayLog
from fluttercomic.models import Comic
from fluttercomic.models import Order
from fluttercomic.api import endpoint_session
from fluttercomic.api.wsgi.token import verify
from fluttercomic.api.wsgi.token import online
from fluttercomic.api.wsgi.utils import format_chapters
from fluttercomic.api.wsgi.controllers import WSPORTS

from fluttercomic.plugin import convert

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CF = CONF[common.NAME]

WEBSOCKETPROC = 'fluttercomic-websocket'

FAULT_MAP = {
    InvalidArgument: webob.exc.HTTPClientError,
    NoResultFound: webob.exc.HTTPNotFound,
    MultipleResultsFound: webob.exc.HTTPInternalServerError
}


WEBSOCKETUPLOAD = {
        'type': 'object',
        'required': ['type', 'fileinfo'],
        'properties':
            {
                'type': {'type': 'string', 'enum': ['websocket']},
                'fileinfo': FILEINFOSCHEMA,
             }
    }


SPIDERUPLOAD = {
        'type': 'object',
        'required': ['type', 'url'],
        'properties':
            {
                'type': {'type': 'string', 'enum': ['spider']},
                'url': {'type': 'string', 'format': 'url'},
                'interval': {'type': 'integer', 'minimum': 0},
                'ext': {'type': 'object'},
             }
    }


@contextlib.contextmanager
def _prepare_comic_path(comic):
    comic_path = ComicRequest.comic_path(comic)
    if os.path.exists(comic_path):
        raise
    os.makedirs(comic_path, 0o755)
    try:
        yield
    except Exception:
        shutil.rmtree(comic_path)


@contextlib.contextmanager
def _prepare_chapter_path(comic, chapter):
    comic_path = ComicRequest.comic_path(comic)
    chapter_path = ComicRequest.chapter_path(comic, chapter)

    if not os.path.exists(comic_path):
        raise
    if not os.path.exists(chapter_path):
        raise

    os.makedirs(chapter_path, 0o755)
    try:
        yield
    except Exception:
        shutil.rmtree(chapter_path)


@singleton.singleton
class ComicRequest(MiddlewareContorller):

    ADMINAPI = False

    NEWCHAPTER = {
        'type': 'object',
        'required': ['impl', 'timeout'],
        'properties':
            {
                 'impl': {'oneOf': [WEBSOCKETUPLOAD, SPIDERUPLOAD]},
                 'timeout': {'type': 'integer', 'minimum': 30, 'maximun': 1200},                   # pagen number
             }
    }

    @staticmethod
    def comic_path(comic):
        return os.path.join(CF.basedir, str(comic))

    @staticmethod
    def chapter_path(comic, chapter):
        return os.path.join(CF.basedir, str(comic), str(chapter))

    def index(self, req, body=None):
        """列出漫画"""
        session = endpoint_session(readonly=True)
        query = model_query(session, Comic)
        return resultutils.results(result='list comics success',
                                   data=[dict(cid=comic.cid,
                                              name=comic.name,
                                              author=comic.author,
                                              type=comic.type,
                                              region=comic.region,
                                              point=comic.point,
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
        with session.begin():
            with _prepare_comic_path():
                session.add(comic)
                session.flush()
        return resultutils.results(result='create comic success', data=[dict(cid=comic.cid, name=comic.name)])

    def show(self, req, cid, body=None):
        """显示漫画详细, 自动确认用户登陆登陆信息"""
        cid = int(cid)
        session = endpoint_session(readonly=True)
        query = model_query(session, Comic, filter=Comic.cid == cid)
        comic = query.one()
        if comic.status < 0:
            raise
        chapters = None
        point = comic.point
        uid, mid = online(req)
        # 管理员
        if mid:
            point = common.MAXCHAPTERS
        #  已登陆,token经过校验
        elif uid:
            query = model_query(session, UserOwn.chapters, filter=and_(UserOwn.uid == uid, UserOwn.cid == cid))
            owns = query.one_or_none()
            if owns:
                chapters = owns.chapters
        elif comic.status == common.HIDE:
            raise
        return resultutils.results(result='show comic success',
                                   data=[dict(cid=comic.cid,
                                              name=comic.name,
                                              author=comic.author,
                                              type=comic.type,
                                              region=comic.region,
                                              point=comic.point,
                                              last=comic.last,
                                              lastup=comic.lastup,
                                              chapters=format_chapters(point, comic.chapters, chapters))])

    @verify(manager=True)
    def update(self, req, cid, body=None):
        pass

    @verify(manager=True)
    def delete(self, req, cid, body=None):
        pass

    @verify(manager=True)
    def cover(self, req, cid, body=None):
        """上传封面"""

        timeout = body.get('timeout')
        fileinfo = body.get('fileinfo')
        jsonutils.schema_validate(fileinfo, FILEINFOSCHEMA)

        comic_path = self.comic_path(cid)

        logfile = '%d.conver.%d.log' % (int(time.time()), cid)
        self._log_path()

        tmpfile = 'main.%d.pic' % int(time.time())
        fileinfo.update({'overwrite': tmpfile})
        tmpfile = os.path.join(comic_path, tmpfile)
        if os.path.exists(tmpfile):
            raise

        port = max(WSPORTS)
        WSPORTS.remove(port)

        def _exitfunc():
            WSPORTS.add(port)
            if not os.path.exists(tmpfile):
                LOG.error('comic cover file not exist')
            else:
                LOG.info('Call shell command convert')
                convert.convert_cover(tmpfile)


        ws = LaunchRecverWebsocket(WEBSOCKETPROC)
        try:
            uri = ws.upload(user=CF.user, group=CF.group,
                            ipaddr=CF.ipaddr, port=port,
                            rootpath=comic_path, fileinfo=fileinfo,
                            logfile=os.path.join(CF.logdir, logfile),
                            timeout=timeout)
            self.manager.websockets.setdefault(ws.pid, WEBSOCKETPROC)
        except Exception:
            WSPORTS.add(port)
            return resultutils.results(result='upload cover get websocket uri fail',
                                       resultcode=manager_common.RESULT_ERROR)
        else:
            ws.asyncwait(exitfunc=_exitfunc)

        return resultutils.results(result='upload cover get websocket uri success',
                                   data=[uri])

    @verify(manager=False)
    def buy(self, req, cid, chapter, uid, body=None):
        """购买一个章节"""
        cid = int(cid)
        chapter = int(chapter)
        uid = int(uid)
        body = body or {}
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
        cid = int(cid)
        uid = int(uid)
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
        cid = int(cid)
        uid = int(uid)
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
        cid = int(cid)
        chapter = int(chapter)
        body = body or {}
        jsonutils.schema_validate(body, self.NEWCHAPTER)

        impl = body.get('impl')
        timeout = body.get('timeout')

        logfile = '%d.chapter.%d.%d.log' % (int(time.time()), cid, chapter)
        comic_path = self.comic_path(cid)
        chapter_path = self.chapter_path(cid, chapter)

        if impl['type'] == 'websocket':
            tmpfile = 'chapter.%d.uploading' % int(time.time())
            fileinfo = impl.get('fileinfo')
            fileinfo.update({'overwrite': tmpfile})
            tmpfile = os.path.join(comic_path, tmpfile)
            if os.path.exists(tmpfile):
                raise
        else:
            raise NotImplementedError

        port = max(WSPORTS)
        WSPORTS.remove(port)

        def _exitfunc():

            WSPORTS.add(port)
            if not os.path.exists(tmpfile):
                LOG.error('comic chapter file not exist')
                self._unfinish(cid, chapter)
            else:
                LOG.info('Check name from upload file')
                # checket chapter file
                count = 0
                for filename in zlibutils.iter_files(tmpfile, common.MAXCHAPTERPIC):
                    count += 1
                    if os.path.splitext(filename)[1] not in common.IMGEXT:
                        raise
                LOG.info('extract upload file to chapter path')
                # extract chapter file
                zlibutils.async_extract(tmpfile, chapter_path)
                LOG.info('convert chapter path')
                try:
                    count = convert.convert_chapter(tmpfile, chapter_path, '%d%s' % (cid, key))
                except Exception:
                    self._unfinish(cid, chapter)
                else:
                    self._finished(cid, chapter, dict(key=key, max=count))



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

            with _prepare_chapter_path(comic.cid, chapter):
                comic.last = chapter
                session.flush()
                # 创建资源url加密key
                key = ''.join(random.sample(string.lowercase, 6))
                # 注意: 下面的操作会导致漫画被锁定较长时间,
                if impl['type'] == 'local':
                    ws = LaunchRecverWebsocket(WEBSOCKETPROC)
                    try:
                        uri = ws.upload(user=CF.user, group=CF.group,
                                        ipaddr=CF.ipaddr, port=port,
                                        rootpath=comic_path, fileinfo=impl['fileinfo'],
                                        logfile=os.path.join(CF.logdir, logfile),
                                        timeout=timeout)
                    except Exception:
                        WSPORTS.add(port)
                        return resultutils.results(result='upload cover get websocket uri fail',
                                                   resultcode=manager_common.RESULT_ERROR)
                    else:

                        ws.asyncwait(exitfunc=_exitfunc)
                        worker = uri
                else:
                    worker = None #  asyncrequest.to_dict()
                    raise NotImplementedError

        return resultutils.results(result='finished update new chapter',
                                   data=[dict(cid=comic.cid, name=comic.name, worker=worker)])

    def _finished(self, cid, chapter, body):
        """章节上传完成 通知开放"""
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
            return comic

    def _unfinish(self, cid, chapter):
        """章节上传完成 失败, 通知还原"""
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
        chapter_path = self.chapter_path(cid, chapter)
        try:
            shutil.rmtree(chapter_path)
        except (OSError, IOError):
            LOG.error('Api _unfinsh Remove chapter path %s fail' % chapter_path)
        return comic

    @verify(manager=True)
    def finished(self, req, cid, chapter, body=None):
        """章节上传完成 通知开放"""
        body = body or {}
        cid = int(cid)
        chapter = int(chapter)
        comic = self._finished(cid, chapter, body)
        return resultutils.results(result='finished comic success', data=[dict(cid=cid, name=comic.name)])

    @verify(manager=True)
    def unfinish(self, req, cid, chapter, body=None):
        body = body or {}
        cid = int(cid)
        chapter = int(chapter)
        comic = self._unfinish(cid, chapter)
        return resultutils.results(result='unfinish comic success', data=[dict(cid=comic.cid, name=comic.name)])
