# -*- coding:utf-8 -*-
from simpleservice.wsgi.middleware import MiddlewareContorller


class PlatformsRequestBase(MiddlewareContorller):

    ADMINAPI = False


    def html(self, req, body=None):
        raise NotImplementedError

    def new(self, req, body=None):
        """发起订单"""
        raise NotImplementedError

    def esure(self, req, oid, body=None):
        raise NotImplementedError
