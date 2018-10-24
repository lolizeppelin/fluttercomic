from simpleutil.config import cfg
from simpleutil.config import types

CONF = cfg.CONF

NAME = 'huawei'

huawei_opts = [
    cfg.ListOpt('huawei',
                item_type=types.String(),
                default=[],
                help='huawei opts'),
]


def register_opts(group):
    CONF.register_opts(huawei_opts, group)
