# -*- coding:utf-8 -*-
import msgpack
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext import declarative

from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.dialects.mysql import SMALLINT
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.dialects.mysql import BLOB

from simpleservice.ormdb.models import TableBase
from simpleservice.ormdb.models import InnoDBTableBase
from simpleservice.ormdb.models import MyISAMTableBase

from simpleutil.utils import uuidutils

from fluttercomic import common

TableBase = declarative.declarative_base(cls=TableBase)

EMPTYLIST = msgpack.packb([])


class Manager(TableBase):
    """管理员信息"""
    mid = sa.Column(INTEGER(unsigned=True), nullable=False,
                    primary_key=True, autoincrement=True)                       # 用户ID
    name = sa.Column(VARCHAR(32), nullable=False)                               # 用户名
    salt = sa.Column(CHAR(6), nullable=False)                                   # 密码盐
    passwd = sa.Column(VARCHAR(64), nullable=False)                             # 密码
    status = sa.Column(TINYINT, nullable=False, default=common.ACTIVE)          # 用户状态
    sopce = sa.Column(VARCHAR(32), nullable=False)                              # 区域

    __table_args__ = (
        InnoDBTableBase.__table_args__
    )


class User(TableBase):
    """用户信息"""
    uid = sa.Column(INTEGER(unsigned=True), nullable=False,
                    primary_key=True, autoincrement=True)                       # 用户ID
    name = sa.Column(VARCHAR(32), nullable=False)                               # 用户名
    salt = sa.Column(CHAR(6), nullable=False)                                   # 密码盐
    passwd = sa.Column(VARCHAR(64), nullable=False)                             # 密码
    coins = sa.Column(INTEGER(unsigned=True), nullable=False, default=0)        # 剩余coin
    gifts = sa.Column(INTEGER(unsigned=True), nullable=False, default=0)        # 代币
    regtime = sa.Column(INTEGER(unsigned=True), nullable=False)                 # 注册时间
    status = sa.Column(TINYINT, nullable=False, default=common.ACTIVE)          # 用户状态
    activecode = sa.Column(INTEGER(unsigned=True), nullable=True)               # 激活验证码'
    books =  orm.relationship('UserBook',
                              primaryjoin='User.uid == UserBook.uid',
                              foreign_keys='UserBook.uid',backref='user', lazy='select')
    owns = orm.relationship('UserOwn',
                              primaryjoin='User.uid == UserOwn.uid',
                              foreign_keys='UserOwn.uid',backref='user', lazy='select')

    __table_args__ = (
        sa.UniqueConstraint('name', name='name_unique'),
        InnoDBTableBase.__table_args__
    )


class Comic(TableBase):
    """漫画信息"""
    cid = sa.Column(INTEGER(unsigned=True), nullable=False,
                    primary_key=True, autoincrement=True)                        # 漫画ID
    status = sa.Column(TINYINT, nullable=False, default=common.ACTIVE)           # 漫画状态,是否下架之类
    name = sa.Column(VARCHAR(128), nullable=False)                               # 漫画名
    author = sa.Column(VARCHAR(128), nullable=False)                             # 作者
    type = sa.Column(VARCHAR(16), nullable=False)                                # 类型
    region = sa.Column(VARCHAR(8), nullable=False)                               # 地区/港台/大陆/日本/欧美
    point = sa.Column(INTEGER(unsigned=True), nullable=False, default=0)         # 条件点
    last = sa.Column(SMALLINT(unsigned=True), nullable=False, default=0)         # 最后章节
    lastup = sa.Column(INTEGER(unsigned=True), nullable=False, default=0)        # 最后更新时间
    chapters = sa.Column(BLOB, nullable=False, default=EMPTYLIST)                # 章节信息

    __table_args__ = (
        sa.Index('name_index', 'name'),
        InnoDBTableBase.__table_args__
    )


class UserBook(TableBase):
    """用户收藏书架"""
    # uid = sa.Column(INTEGER(unsigned=True),
    uid = sa.Column(sa.ForeignKey('user.uid'),
                    nullable=False, primary_key=True)                                           # 用户ID
    cid = sa.Column(INTEGER(unsigned=True), nullable=False,
                    primary_key=True)                                           # 漫画ID
    name = sa.Column(VARCHAR(128), nullable=False)                              # 漫画名
    author = sa.Column(VARCHAR(128), nullable=False)                            # 漫画作者
    time = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 收藏时间

    __table_args__ = (
        InnoDBTableBase.__table_args__
    )


class UserOwn(TableBase):
    """用户拥有漫画章节"""
    # uid = sa.Column(INTEGER(unsigned=True), nullable=False,
    uid = sa.Column(sa.ForeignKey('user.uid'),
                    nullable=False, primary_key=True)                                           # 用户ID
    cid = sa.Column(INTEGER(unsigned=True), nullable=False,
                    primary_key=True)                                           # 漫画ID
    chapters = sa.Column(BLOB, nullable=False, default=EMPTYLIST)               # 拥有章节

    __table_args__ = (
        InnoDBTableBase.__table_args__
    )


class UserPayLog(TableBase):
    """用户购买章节记录, 可用于还原UserOwn"""
    uid = sa.Column(INTEGER(unsigned=True), nullable=False,
                    primary_key=True)                                           # 用户ID
    cid = sa.Column(INTEGER(unsigned=True), nullable=False,
                    primary_key=True)                                           # 漫画ID
    chapter = sa.Column(INTEGER(unsigned=True), nullable=False,
                        primary_key=True)                                       # 章节
    value = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 总消耗
    coin = sa.Column(SMALLINT(unsigned=True), nullable=False)                   # 购买用coin
    gift = sa.Column(SMALLINT(unsigned=True), nullable=False)                   # 购买用gift
    coins = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 购买时coins(加锁,准确)
    gifts = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 购买时gifts(加锁,准确)
    time = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 购买时间

    __table_args__ = (
        MyISAMTableBase.__table_args__
    )


class Order(TableBase):
    """预备订单"""
    oid = sa.Column(BIGINT(unsigned=True), nullable=False,
                    default=uuidutils.Gkey, primary_key=True)                   # 订单ID
    uid = sa.Column(INTEGER(unsigned=True), nullable=False)                     # 用户id
    coins = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 订单发起时用户coins(不加锁,有可能不准)
    gifts = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 订单发起时用户gifts(不加锁,有可能不准)
    coin = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 订单coin数量
    gift = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 订单gift数量
    money = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 金钱数量
    platform = sa.Column(VARCHAR(32), nullable=True)                            # 订单类型平台
    serial = sa.Column(VARCHAR(128), nullable=True)                             # 流水号
    time = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 订单时间
    cid = sa.Column(INTEGER(unsigned=True), nullable=False, default=0)          # 订单发起时用户所看漫画
    chapter = sa.Column(INTEGER(unsigned=True), nullable=False, default=0)      # 订单发起时用户所看章节
    ext = sa.Column(BLOB, nullable=True)                                        # 扩展信息

    __table_args__ = (
        sa.UniqueConstraint('serial', name='serial_unique'),
        sa.Index('type_platform', 'platform'),
        MyISAMTableBase.__table_args__
    )


class RechargeLog(TableBase):
    """成功充值票据"""
    oid = sa.Column(BIGINT(unsigned=True), nullable=False,
                    primary_key=True)                                           # 订单ID
    uid = sa.Column(INTEGER(unsigned=True), nullable=False)                     # 用户id
    coins = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 完成充值前用户coins(加锁,准确)
    gifts = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 完成充值前用户gifts(加锁,准确)
    coin = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 订单coin数量
    gift = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 订单gift数量
    money = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 金钱数量
    platform = sa.Column(VARCHAR(32), nullable=True)                            # 订单类型平台
    time = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 完成时间
    cid = sa.Column(INTEGER(unsigned=True), nullable=False, default=0)          # 订单发起时用户所看漫画
    chapter = sa.Column(INTEGER(unsigned=True), nullable=False, default=0)      # 订单发起时用户所看章节
    __table_args__ = (
        MyISAMTableBase.__table_args__
    )


class DuplicateRecharge(TableBase):
    """重复支付"""
    id = sa.Column(BIGINT(unsigned=True), nullable=False,
                   primary_key=True, autoincrement=True)
    oid = sa.Column(BIGINT(unsigned=True), nullable=False)                      # 订单ID
    coin = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 订单coin数量
    gift = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 订单gift数量
    money = sa.Column(INTEGER(unsigned=True), nullable=False)                   # 金钱数量
    time = sa.Column(INTEGER(unsigned=True), nullable=False)                    # 重复时间

    __table_args__ = (
        MyISAMTableBase.__table_args__
    )
