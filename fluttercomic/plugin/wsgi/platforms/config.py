from simpleutil.config import cfg
from simpleutil.config import types

CONF = cfg.CONF

platforms_opts = [
    cfg.ListOpt('platforms',
                item_type=types.String(),
                default=[],
                help='Platforms list enabled'),
]


def register_opts(group):
    CONF.register_opts(platforms_opts, group)
