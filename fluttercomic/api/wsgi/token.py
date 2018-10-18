# -*- coding: UTF-8 -*-

from simpleservice import common as service_common

from goperation.manager import exceptions
from goperation.manager.tokens import TokenProvider

M = object()    # 管理员接口
U = object()    # 普通用户接口


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

    def __call__(self, req, **kwargs):
        # 普通用户必须是fernet token
        if self.vtype is U and not TokenProvider.is_fernet(req):
            raise exceptions.TokenError('Not fernet token')
        try:
            token = TokenProvider.token(req)
        except KeyError:
            # 未经认证拦截器校验
            raise exceptions.TokenError('Token not verify or none')
        if self.vtype is M and not token.get('mid'):
            raise exceptions.TokenError('No manager found in token')
        else:
            if self.vtype is not M and 'uid' in kwargs and (kwargs.get('uid') != str(token.get('uid'))):
                raise exceptions.TokenError('Uid not match')
        return self.func(req, **kwargs)
