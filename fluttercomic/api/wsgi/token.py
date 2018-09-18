# -*- coding: UTF-8 -*-

from simpleservice import common as service_common

from goperation.manager import exceptions
from goperation.manager.tokens import TokenProvider


def verify(manager=True):
    """装饰器, 用于接口校验"""

    def _check(func):
        return TokenVerify(func, manager)

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
    def __init__(self, func=None, manager=False):
        self.func = func
        self.manager = manager

    def __get__(self, instance, owner):
        if hasattr(self.func, '__get__'):
            return self.func.__get__(instance, owner)
        return self

    def __call__(self, req, **kwargs):
        if not self.manager and not TokenProvider.is_fernet(req):
            raise exceptions.TokenError('Not fernet token')
        try:
            token = TokenProvider.token(req)
        except KeyError:
            # 未经认证拦截器校验
            raise exceptions.TokenError('Token not verify or none')
        if self.manager and not token.get('mid'):
            raise
        else:
            if 'uid' in kwargs and (kwargs.get('uid') != str(token.get('uid'))):
                raise
        return self.func(req, **kwargs)
