# -*- coding:utf-8 -*-
import time
import webob.exc
from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

from simpleutil.log import log as logging
from simpleutil.utils import argutils
from simpleutil.utils import singleton

from simpleutil.common.exceptions import InvalidArgument

from simpleservice.ormdb.api import model_query
from simpleservice.wsgi.middleware import MiddlewareContorller


from goperation import threadpool
from goperation.manager.utils import resultutils

from fluttercomic.api.wsgi.token import verify
from fluttercomic.plugin.platforms.base import PlatformsRequestBase


LOG = logging.getLogger(__name__)

FAULT_MAP = {InvalidArgument: webob.exc.HTTPClientError,
             NoResultFound: webob.exc.HTTPNotFound,
             MultipleResultsFound: webob.exc.HTTPInternalServerError}



@singleton.singleton
class HuaweiRequest(PlatformsRequestBase):

    ADMINAPI = False

    @verify()
    def new(self, req, body=None):
        """发起订单"""
        raise NotImplementedError


    def esure(self, req, oid, body=None):
        raise NotImplementedError


