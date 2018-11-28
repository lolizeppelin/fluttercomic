# -*- coding:utf-8 -*-
from simpleutil.config import cfg
from simpleutil.utils import singleton
from simpleservice.wsgi.middleware import MiddlewareContorller

from goperation.manager.utils import resultutils

from fluttercomic import common

CONF = cfg.CONF


@singleton.singleton
class PlatformsRequestPublic(MiddlewareContorller):

    __conf = CONF[common.NAME]

    ADMINAPI = False

    def platforms(self):
        return resultutils.results(result='get platforms success',
                                   data=self.__conf.platforms)



class PlatformsRequestBase(MiddlewareContorller):

    ADMINAPI = False


    def html(self, req, body=None):
        raise NotImplementedError

    def new(self, req, body=None):
        """发起订单"""
        raise NotImplementedError

    def esure(self, req, oid, body=None):
        raise NotImplementedError
