from simpleutil.config import cfg
from simpleutil.config import types

from fluttercomic.plugin import platforms

CONF = cfg.CONF

platforms_opts = [
    cfg.ListOpt('platforms',
                item_type=types.String(),
                default=[],
                help='Platforms list enabled'),
]

platform_opts = [
    cfg.BoolOpt('sandbox',
                default=True,
                help='paypal is sandbox api, just for send to paypal sandbox'),
    cfg.FloatOpt('roe',
                default=1.0,
                help='money rate of exchange, do not change this value if you don not what for'),
    cfg.IntOpt('scale',
               default=100,
               help='scale for money to coins'),
    cfg.StrOpt('currency',
               default='USD',
               help='Pay currency type'),
    cfg.ListOpt('choices',
                default=[],
                item_type=types.Integer(),
                help='Pay money choice')
]


def register_opts(group):
    CONF.register_opts(platforms_opts, group)


def register_platform(name, choices, scale, currency, **kwargs):
    base_opt = dict(choices=choices, scale=scale, currency=currency)
    base_opt.update(kwargs)
    platforms.Platforms[name] = base_opt
