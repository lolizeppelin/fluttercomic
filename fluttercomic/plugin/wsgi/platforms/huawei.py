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


LOG = logging.getLogger(__name__)

FAULT_MAP = {InvalidArgument: webob.exc.HTTPClientError,
             NoResultFound: webob.exc.HTTPNotFound,
             MultipleResultsFound: webob.exc.HTTPInternalServerError}



@singleton.singleton
class HuaweiRequest(MiddlewareContorller):

    ADMINAPI = False


    def pay(self, req, oid, body=None):
        """支付订单"""


