# -*- coding: UTF-8 -*-
from simpleservice import common as service_common

from goperation.manager import exceptions
from goperation.manager.tokens import TokenProvider

M = object()    # 管理员接口
U = object()    # 普通用户接口
B = object()    # 普通用户/管理员 通用接口


def verify(vtype=U):
    """装饰器, 用于接口校验"""

    def _check(func):
        return TokenVerify(func, vtype)

    return _check


def online(req):
    """登陆用户信息"""
    try:
        token = TokenProvider.token(req)
    except KeyError:
        # 没有经过认证拦截器的必须是fernet token
        if not TokenProvider.is_fernet(req):
            return None, None
        token_id = req.headers.get(service_common.TOKENNAME.lower())
        if not token_id:
            # 为登陆用户
            return None, None
        # 解析fernet token
        token = TokenProvider.fetch(req, token_id)
    return token.get('uid'), token.get('mid')


class TokenVerify(object):
    """This Descriptor code copy from Wsgify
    """
    def __init__(self, func, vtype):
        self.func = func
        self.vtype = vtype

    def __get__(self, instance, owner):
        if hasattr(self.func, '__get__'):
            # return self.func.__get__(instance, owner)
            self.func = self.func.__get__(instance, owner)
        return self

    @staticmethod
    def _validate_uid(kwargs, token):
        if int(kwargs.get('uid')) != token.get('uid'):
            raise exceptions.TokenError('Token uid not match with value in kwargs')

    def __call__(self, req, **kwargs):
        try:
            token = TokenProvider.token(req)
        except KeyError:
            # 未经认证拦截器校验
            raise exceptions.TokenError('Token not verify or none')
        if self.vtype is M:
            if not token.get('mid'):
                raise exceptions.TokenError('No manager found in token')
        elif self.vtype is U:
            if not TokenProvider.is_fernet(req):
                raise exceptions.TokenError('Not fernet token')
            self._validate_uid(kwargs, token)
        else:
            if TokenProvider.is_fernet(req):
                self._validate_uid(kwargs, token)
        return self.func(req, **kwargs)
