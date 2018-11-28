# -*- coding:utf-8 -*-
import time
import webob.exc
from sqlalchemy.sql import and_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound

from simpleutil.log import log as logging
from simpleutil.utils import singleton
from simpleutil.utils import jsonutils

from simpleutil.common.exceptions import InvalidArgument

from simpleservice.ormdb.api import model_query
from simpleservice.wsgi.middleware import MiddlewareContorller

from goperation.manager.exceptions import TokenError
from goperation.manager import common as manager_common
from goperation.manager.utils import resultutils

from fluttercomic.api import endpoint_session
from fluttercomic.api.wsgi.token import verify
from fluttercomic.api.wsgi.token import M

from fluttercomic.models import Order
from fluttercomic.models import RechargeLog
from fluttercomic.models import DuplicateRecharge


LOG = logging.getLogger(__name__)

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
class OrderRequest(MiddlewareContorller):

    ADMINAPI = False

    @verify(vtype=M)
    def index(self, req, body=None):
        """列出订单"""
        body = body or {}
        session = endpoint_session(readonly=True)
        sandbox = int(body.pop('sandbox', False))
        platform = body.pop('platform', None)
        oid = body.pop('oid', None)

        filters = [Order.sandbox == sandbox]
        if platform:
            filters.insert(0, Order.platform == platform)
        if oid:
            filters.insert(0, Order.oid < oid)
        filters = filters[0] if len(filters) == 1 else and_(*filters)

        ret_dict = resultutils.bulk_results(session,
                                            model=Order,
                                            columns=[Order.oid,
                                                     Order.platform,
                                                     Order.uid,
                                                     Order.coin,
                                                     Order.gift,
                                                     Order.money,
                                                     Order.platform,
                                                     Order.time,
                                                     ],
                                            counter=Order.oid,
                                            order=Order.oid, desc=True,
                                            filter=filters,
                                            limit=1000)
        return ret_dict

    @verify(vtype=M)
    def show(self, req, oid, body=None):
        """订单详情"""
        body = body or {}
        oid = int(oid)
        session = endpoint_session(readonly=True)
        query = model_query(session, Order, filter=Order.oid == oid)
        order = query.one()
        return resultutils.results(result='show order success',
                                   data=[
                                       dict(
                                           oid=order.oid,
                                           sandbox=order.sandbox,
                                           uid=order.uid,
                                           coins=order.coins,
                                           gifts=order.gifts,
                                           coin=order.coin,
                                           gift=order.gift,
                                           money=order.money,
                                           platform=order.platform,
                                           serial=order.serial,
                                           time=order.time,
                                           cid=order.cid,
                                           chapter=order.chapter,
                                           ext=jsonutils.loads_as_bytes(order.ext) if order.ext else None,
                                       )
                                   ])


@singleton.singleton
class RechargeRequest(MiddlewareContorller):

    ADMINAPI = False

    @verify(vtype=M)
    def index(self, req, body=None):
        """列出完成订单"""
        body = body or {}
        session = endpoint_session(readonly=True)
        sandbox = int(body.pop('sandbox', False))
        platform = body.pop('platform', None)
        oid = body.pop('oid', None)

        filters = [RechargeLog.sandbox == sandbox]
        if platform:
            filters.insert(0, RechargeLog.platform == platform)
        if oid:
            filters.insert(0, RechargeLog.oid < oid)
        filters = filters[0] if len(filters) == 1 else and_(*filters)

        ret_dict = resultutils.bulk_results(session,
                                            model=RechargeLog,
                                            columns=[RechargeLog.oid,
                                                     RechargeLog.platform,
                                                     RechargeLog.uid,
                                                     RechargeLog.coin,
                                                     RechargeLog.gift,
                                                     RechargeLog.money,
                                                     RechargeLog.platform,
                                                     RechargeLog.time,
                                                     ],
                                            counter=RechargeLog.oid,
                                            order=RechargeLog.oid, desc=True,
                                            filter=filters,
                                            limit=1000)
        return ret_dict

    @verify(vtype=M)
    def show(self, req, oid, body=None):
        """完成订单详情"""
        body = body or {}
        oid = int(oid)
        session = endpoint_session(readonly=True)
        query = model_query(session, RechargeLog, filter=RechargeLog.oid == oid)
        relog = query.one()
        return resultutils.results(result='show recharge log success',
                                   data=[
                                       dict(
                                           oid=relog.oid,
                                           sandbox=relog.sandbox,
                                           uid=relog.uid,
                                           coins=relog.coins,
                                           gifts=relog.gifts,
                                           coin=relog.coin,
                                           gift=relog.gift,
                                           money=relog.money,
                                           platform=relog.platform,
                                           serial=relog.serial,
                                           time=relog.time,
                                           cid=relog.cid,
                                           chapter=relog.chapter,
                                           ext=jsonutils.loads_as_bytes(relog.ext) if relog.ext else None,
                                       )
                                   ])