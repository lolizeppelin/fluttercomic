# -*- coding:utf-8 -*-
import os
import time
import random
import string
import webob.exc
import msgpack
import eventlet

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
from goperation.manager.exceptions import TokenError
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
from fluttercomic.api.wsgi.token import M
from fluttercomic.api.wsgi.token import online
from fluttercomic.api.wsgi.utils import format_chapters
from fluttercomic.api.wsgi.controllers import WSPORTS

from fluttercomic.plugin import convert
from fluttercomic.api import exceptions

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CF = CONF[common.NAME]

WEBSOCKETPROC = 'fluttercomic-websocket'

FAULT_MAP = {
    InvalidArgument: webob.exc.HTTPClientError,
    NoResultFound: webob.exc.HTTPNotFound,
    TokenError: webob.exc.HTTPUnauthorized,
    MultipleResultsFound: webob.exc.HTTPInternalServerError
}

COVERUPLOAD = {
    'type': 'object',
    'required': ['fileinfo'],
    'properties':
        {
            'timeout': {'type': 'integer', 'minimum': 5, 'maximun': 30},
            'fileinfo': FILEINFOSCHEMA,
         }
}

# 从websocket上传漫画
WEBSOCKETUPLOAD = {
        'type': 'object',
        'required': ['type', 'fileinfo'],
        'properties':
            {
                'type': {'type': 'string', 'enum': ['websocket']},
                'fileinfo': FILEINFOSCHEMA,
             }
    }
# 漫画在本地文件夹
LOCAL = {
        'type': 'object',
        'required': ['type', 'path'],
        'properties':
            {
                'type': {'type': 'string', 'enum': ['local']},
                'path': {'type': 'string', 'minLength': 2},
             }
    }
# 直接用爬
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

NEWCHAPTER = {
    'type': 'object',
    'required': ['impl', 'timeout'],
    'properties':
        {
             'impl': {'oneOf': [WEBSOCKETUPLOAD, SPIDERUPLOAD, LOCAL]},
             'timeout': {'type': 'integer', 'minimum': 30, 'maximun': 1200},                   # pagen number
         }
}

NEWCOMIC = {
    'type': 'object',
    'required': ['name', 'type', 'region', 'author'],
    'properties':
        {
             'name': {'type': 'string', 'minLength': 2, 'maxLength': 128},
             'type': {'type': 'string', 'minLength': 2, 'maxLength': 16},
             'region': {'type': 'string', 'minLength': 2, 'maxLength': 8},
             'author': {'type': 'string', 'minLength': 2, 'maxLength': 128},
             'ext': {'type': 'string', 'enum': ['webp', 'jpg', 'png']},
         }
}

class _prepare_comic_path(object):

    def __init__(self):
        self._path = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and self._path:
            try:
                shutil.rmtree(self._path)
            except (OSError, IOError):
                LOG.error('Prepare comic error, remove %s fail')

    def ok(self, cid):
        path = ComicRequest.comic_path(cid)
        if os.path.exists(path):
            raise exceptions.ComicFolderError('Comic path alreday exist')
        os.makedirs(path, 0o755)
        self._path = path


@contextlib.contextmanager
def _prepare_chapter_path(comic, chapter):
    comic_path = ComicRequest.comic_path(comic)
    chapter_path = ComicRequest.chapter_path(comic, chapter)

    if not os.path.exists(comic_path):
        raise exceptions.ComicFolderError('Comic path not exist')
    if os.path.exists(chapter_path):
        raise exceptions.ComicFolderError('Chapter path alreday exist')

    os.makedirs(chapter_path, 0o755)
    try:
        yield
    except Exception:
        shutil.rmtree(chapter_path)


@singleton.singleton
class ComicRequest(MiddlewareContorller):

    ADMINAPI = False

    cdndir = os.path.join(CF.basedir, 'cdn')
    logdir  = os.path.join(CF.basedir, 'log')
    tmpdir = os.path.join(CF.basedir, 'tmp')

    def __init__(self):

        if not os.path.exists(self.cdndir):
            os.makedirs(self.cdndir, 0o755)
        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir, 0o755)
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir, 0o755)

    @staticmethod
    def comic_path(comic):
        return os.path.join(ComicRequest.cdndir, str(comic))

    @staticmethod
    def chapter_path(comic, chapter):
        return os.path.join(ComicRequest.cdndir, str(comic), str(chapter))

    @staticmethod
    def _convert_new_chapter_from_dir(src, dst):
        count = 0
        for root, dirs, files in os.walk(src, topdown=True):
            if dirs:
                LOG.error('folder %s in local new chaper path' % dir)
                raise ValueError('folder %s in local new chaper path' % dir)
            if not files:
                raise exceptions.ComicUploadError('No file in path %s')
            for filename in files:
                count += 1
                if count > common.MAXCHAPTERPIC:
                    LOG.error('Chapter img count over size')
                    raise ValueError('Chapter img count over size')
                try:
                    os.rename(os.path.join(src, filename), os.path.join(dst, filename))
                except (OSError, IOError):
                    raise
        return count

    @staticmethod
    def _convert_new_chapter_from_file(src, dst):
        count = 0
        if not os.path.exists(src):
            raise ValueError('Comic chapter file not exist')
        LOG.info('Check name from upload file')
        for filename in zlibutils.iter_files(src):
            count += 1
            if count > common.MAXCHAPTERPIC:
                raise ValueError('Too many file in one chapter')
            ext = os.path.splitext(filename)[1]
            if ext.lower() not in common.IMGEXT:
                raise ValueError('%s not end with img ext' % filename)
        LOG.info('extract upload file to chapter path')
        # extract chapter file
        try:
            zlibutils.async_extract(src, dst).wait()
        finally:
            os.remove(src)
        LOG.info('extract chapter file success')
        return count

    def _convert_new_chapter(self, src, cid, ext, chapter, key, logfile):
        chapter_path = self.chapter_path(cid, chapter)
        if os.path.isdir(src):
            count = self._convert_new_chapter_from_dir(src, chapter_path)
        else:
            count = self._convert_new_chapter_from_file(src, chapter_path)
        _key ='%d%s' % (cid, key)
        convert.convert_chapter(dst=chapter_path, ext=ext, key=_key, logfile=logfile)
        LOG.info('convert chapter path finish')
        return count

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
                                              ext=comic.ext,
                                              lastup=comic.lastup)
                                         for comic in query])

    @verify(vtype=M)
    def create(self, req, body=None):
        """创建新漫画"""
        body = body or {}
        jsonutils.schema_validate(body, NEWCOMIC)
        name = body.get('name')
        type = body.get('type')
        region = body.get('region')
        author = body.get('author')
        ext = body.get('ext', 'webp')

        session = endpoint_session()
        comic = Comic(name=name, type=type, author=author, region=region, ext=ext)
        with _prepare_comic_path() as prepare:
            with session.begin():
                session.add(comic)
                session.flush()
                prepare.ok(comic.cid)
                LOG.info('Create comic success')
        return resultutils.results(result='create comic success', data=[dict(cid=comic.cid, name=comic.name)])

    def show(self, req, cid, body=None):
        """显示漫画详细, 自动确认用户登陆登陆信息"""
        cid = int(cid)
        session = endpoint_session(readonly=True)
        query = model_query(session, Comic, filter=Comic.cid == cid)
        comic = query.one()
        if comic.status < 0:
            raise exceptions.ComicError('Comic status error')
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
            raise exceptions.ComicError('Comic status error')
        return resultutils.results(result='show comic success',
                                   data=[dict(cid=comic.cid,
                                              name=comic.name,
                                              author=comic.author,
                                              type=comic.type,
                                              region=comic.region,
                                              point=comic.point,
                                              last=comic.last,
                                              lastup=comic.lastup,
                                              ext=comic.ext,
                                              chapters=format_chapters(point, comic.chapters, chapters))])

    @verify(vtype=M)
    def update(self, req, cid, body=None):
        raise NotImplementedError

    @verify(vtype=M)
    def delete(self, req, cid, body=None):
        raise NotImplementedError

    @verify(vtype=M)
    def cover(self, req, cid, body=None):
        """上传封面"""
        cid = int(cid)
        jsonutils.schema_validate(body, COVERUPLOAD)
        timeout = body.get('timeout', 20)
        fileinfo = body.get('fileinfo')

        comic_path = self.comic_path(cid)

        logfile = '%d.conver.%d.log' % (int(time.time()), cid)
        logfile = os.path.join(self.logdir, logfile)
        tmpfile = 'main.%d.pic' % int(time.time())
        fileinfo.update({'overwrite': tmpfile})
        tmpfile = os.path.join(comic_path, tmpfile)
        if os.path.exists(tmpfile):
            raise exceptions.ComicUploadError('Upload cover file fail')

        session = endpoint_session(readonly=True)
        query = model_query(session, Comic, filter=Comic.cid == cid)
        comic = query.one()
        rename = 'main.%s' % comic.ext

        port = max(WSPORTS)
        WSPORTS.remove(port)

        def _exitfunc():
            WSPORTS.add(port)
            if not os.path.exists(tmpfile):
                LOG.error('comic cover file %s not exist' % tmpfile)
            else:
                LOG.info('Call shell command convert')
                convert.convert_cover(tmpfile, rename=rename, logfile=logfile)
                LOG.info('Convert execute success')
        ws = LaunchRecverWebsocket(WEBSOCKETPROC)
        try:
            uri = ws.upload(user=CF.user, group=CF.group,
                            ipaddr=CF.ipaddr, port=port,
                            rootpath=comic_path, fileinfo=fileinfo,
                            logfile=logfile,
                            timeout=timeout)
        except Exception:
            WSPORTS.add(port)
            return resultutils.results(result='upload cover get websocket uri fail',
                                       resultcode=manager_common.RESULT_ERROR)
        else:
            ws.asyncwait(exitfunc=_exitfunc)

        return resultutils.results(result='upload cover get websocket uri success',
                                   data=[uri])

    @verify()
    def buy(self, req, cid, chapter, uid, body=None):
        """购买一个章节"""
        cid = int(cid)
        chapter = int(chapter)
        uid = int(uid)
        session = endpoint_session()
        query = model_query(session, Comic, filter=Comic.cid == cid)
        uquery = session.query(User).filter(User.uid == uid).with_for_update(nowait=True)
        oquery = model_query(session, UserOwn, filter=and_(UserOwn.uid == uid, UserOwn.cid == cid))
        comic = query.one()
        with session.begin():
            if comic.point >= chapter:
                raise InvalidArgument('Do not buy free chaper')
            if comic.last < chapter:
                raise InvalidArgument('Do not buy not exist chaper')
            user = uquery.one()

            coins = coin = user.coins
            gifts = gift = user.gifts
            if coin + gift < common.ONECHAPTER:
                raise InvalidArgument('Not enough coin')
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
                owns = UserOwn(uid=uid, cid=cid, ext=comic.ext, chapters=msgpack.packb([chapter, ]))
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
                                              ext=comic.ext,
                                              chapters=format_chapters(comic.point,
                                                                       comic.chapters,
                                                                       owns.chapters))])

    @verify()
    def mark(self, req, cid, uid, body=None):
        """收藏漫画"""
        cid = int(cid)
        uid = int(uid)
        session = endpoint_session()
        if model_count_with_key(session, UserBook, filter=UserBook.uid == uid) >= common.MAXBOOKS:
            raise InvalidArgument('Mark over 50')
        query = model_query(session, Comic.name, filter=Comic.cid == cid)
        comic = query.one()
        try:
            session.add(UserBook(uid=uid, cid=cid, ext=comic.ext, name=comic.name, time=int(time.time())))
            session.flush()
        except DBDuplicateEntry:
            LOG.warning('User alreday mark comic')
        return resultutils.results(result='mark book success',
                                   data=[dict(cid=comic.cid, name=comic.name)])

    @verify()
    def unmark(self, req, cid, uid, body=None):
        """取消收藏"""
        cid = int(cid)
        uid = int(uid)
        session = endpoint_session()
        query = model_query(session, UserBook, filter=and_(UserBook.uid == uid, UserBook.cid == cid))
        book = query.one_or_none()
        if book:
            query.delete(book)
            session.flush()
        return resultutils.results(result='unmark book success')

    @verify(vtype=M)
    def new(self, req, cid, chapter, body=None):
        """添加新章节"""
        cid = int(cid)
        chapter = int(chapter)
        body = body or {}
        jsonutils.schema_validate(body, NEWCHAPTER)
        impl = body.get('impl')
        timeout = body.get('timeout')
        logfile = os.path.join(self.logdir, '%d.chapter.%d.%d.log' %
                               (int(time.time()), cid, chapter))
        comic_path = self.comic_path(cid)
        # 创建资源url加密key
        key = ''.join(random.sample(string.lowercase, 6))

        ext = ''

        if impl['type'] == 'websocket':
            tmpfile = 'chapter.%d.uploading' % int(time.time())
            fileinfo = impl.get('fileinfo')
            fileinfo.update({'overwrite': tmpfile})
            tmpfile = os.path.join(comic_path, tmpfile)
            if os.path.exists(tmpfile):
                raise exceptions.ComicUploadError('Upload chapter file fail')
            try:
                port = WSPORTS.pop()
            except KeyError:
                raise InvalidArgument('Too many websocket process')

            def _websocket_func():
                WSPORTS.add(port)
                LOG.info('Try convert new chapter %d.%d from file:%s, type %s' % (cid, chapter, tmpfile, ext))
                # checket chapter file
                try:
                    count = self._convert_new_chapter(tmpfile, cid, ext, chapter, key, logfile)
                except Exception as e:
                    LOG.error('convert new chapter from websocket upload file fail')
                    self._unfinish(cid, chapter)
                    try:
                        if os.path.exists(tmpfile):
                            os.remove(tmpfile)
                    except (OSError, IOError):
                        LOG.error('Revmove websocket uploade file %s fail' % tmpfile)
                    raise e
                else:
                    self._finishe(cid, chapter, dict(max=count, key=key))
        elif impl['type'] == 'local':
            path = impl['path']
            if '.' in path:
                raise InvalidArgument('Dot is not allow in path')
            if path.startswith('/'):
                raise InvalidArgument('start with / is not allow')
            path = os.path.join(self.tmpdir, path)
            if not os.path.exists(path) or not os.path.isdir(path):
                raise InvalidArgument('Target path %s not exist' % path)

            def _local_func():
                LOG.info('Try convert new chapter %d.%d from path:%s, type %s' % (cid, chapter, tmpfile, ext))
                try:
                    count = self._convert_new_chapter(path, cid, ext, chapter, key, logfile)
                except Exception as e:
                    LOG.error('convert new chapter from local dir %s fail, %s' % (path, e.__class__.__name__))
                    LOG.debug(e.message)
                    self._unfinish(cid, chapter)
                    raise
                else:
                    self._finishe(cid, chapter, dict(max=count, key=key))
        else:
            raise NotImplementedError


        session = endpoint_session()
        query = session.query(Comic).filter(Comic.cid == cid).with_for_update()

        worker = None

        with _prepare_chapter_path(cid, chapter):
            with session.begin():
                comic = query.one()
                LOG.info('Crate New chapter of %d' % cid)
                last = comic.last
                if (last +1) != chapter:
                    raise InvalidArgument('New chapter value  error')

                chapters = msgpack.unpackb(comic.chapters)
                if len(chapters) != comic.last:
                    LOG.error('Comic chapter is uploading')
                    raise InvalidArgument('Comic chapter is uploading')
                comic.last = chapter
                session.flush()
                ext = comic.ext
                # 注意: 下面的操作会导致漫画被锁定较长时间,
                if impl['type'] == 'websocket':
                    ws = LaunchRecverWebsocket(WEBSOCKETPROC)
                    try:
                        uri = ws.upload(user=CF.user, group=CF.group,
                                        ipaddr=CF.ipaddr, port=port,
                                        rootpath=comic_path, fileinfo=impl['fileinfo'],
                                        logfile=logfile,
                                        timeout=timeout)
                    except Exception:
                        WSPORTS.add(port)
                        return resultutils.results(result='upload cover get websocket uri fail',
                                                   resultcode=manager_common.RESULT_ERROR)
                    else:

                        ws.asyncwait(exitfunc=_websocket_func)
                        worker = uri
                    LOG.info('New chapter from websocket port %d' % port)
                elif impl['type'] == 'local':
                    LOG.info('New chapter from local path %s, spawning' % path)
                    eventlet.spawn(_local_func)
                else:
                    raise NotImplementedError

        return resultutils.results(result='new chapter spawning',
                                   data=[dict(cid=comic.cid, name=comic.name, worker=worker)])

    def finished(self, req, cid, chapter, body=None):
        session = endpoint_session(readonly=True)
        query = session.query(Comic).filter(Comic.cid == cid)
        comic = query.one()
        if comic.last < chapter:
            return resultutils.results(result='chapter is unfinish', resultcode=manager_common.RESULT_ERROR)
        elif comic.last == chapter:
            if len(msgpack.unpackb(comic.chapters)) != chapter:
                return resultutils.results(result='chapter is unfinish', resultcode=manager_common.RESULT_ERROR)
        return resultutils.results(result='chapter is finish')

    @staticmethod
    def _finishe(cid, chapter, body):
        """章节上传完成 通知开放"""
        max = body.get('max')           # 章节最大页数
        key = body.get('key')           # 加密key
        session = endpoint_session()
        query = session.query(Comic).filter(Comic.cid == cid).with_for_update()
        with session.begin():
            comic = query.one()
            last = comic.last
            if last != chapter:
                raise InvalidArgument('Finish chapter value error')
            chapters = msgpack.unpackb(comic.chapters)
            if len(chapters) != (last - 1):
                LOG.error('Comic chapter is not uploading, do not finish it')
                raise InvalidArgument('Finish chapter value error')
            chapters.append([max, key])
            comic.lastup = int(time.time())
            comic.chapters = msgpack.packb(chapters)
            session.flush()
            return comic

    @staticmethod
    def _unfinish(cid, chapter):
        """章节上传完成 失败, 通知还原"""
        session = endpoint_session()
        query = session.query(Comic).filter(Comic.cid == cid).with_for_update()
        with session.begin():
            comic = query.one()
            last = comic.last
            if last != chapter:
                raise InvalidArgument('Unfinish chapter value error')
            chapters = msgpack.unpackb(comic.chapters)
            if len(chapters) != (last - 1):
                LOG.error('Comic chapters is not uploading')
                raise InvalidArgument('Unfinish chapter value error')
            comic.last = last - 1
            session.flush()
        chapter_path = ComicRequest.chapter_path(cid, chapter)
        try:
            shutil.rmtree(chapter_path)
        except (OSError, IOError):
            LOG.error('Api _unfinsh Remove chapter path %s fail' % chapter_path)
        return comic

    # @verify(manager=True)
    # def finished(self, req, cid, chapter, body=None):
    #     """章节上传完成 通知开放"""
    #     body = body or {}
    #     cid = int(cid)
    #     chapter = int(chapter)
    #     comic = self._finished(cid, chapter, body)
    #     return resultutils.results(result='finished comic success', data=[dict(cid=cid, name=comic.name)])
    #
    # @verify(manager=True)
    # def unfinish(self, req, cid, chapter, body=None):
    #     body = body or {}
    #     cid = int(cid)
    #     chapter = int(chapter)
    #     comic = self._unfinish(cid, chapter)
    #     return resultutils.results(result='unfinish comic success', data=[dict(cid=comic.cid, name=comic.name)])
