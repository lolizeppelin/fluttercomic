from simpleutil.config import cfg
from simpleutil.config import types

from fluttercomic import common

CONF = cfg.CONF

NAME = '%s.paypal' % common.NAME


group = cfg.OptGroup(name=NAME, title='Fluttercomic Pay platform paypal')

paypal_opts = [
    cfg.StrOpt('clientID',
               help='paypal clientID'),
    cfg.StrOpt('secret',
               help='paypal secret'),
    cfg.BoolOpt('sandbox',
                default=True,
                help='paypal is sandbox api, just for send to paypal sandbox'),
    cfg.FloatOpt('scale',
                default=1.0,
                help='money scale, do not change this value if you don not what for'),
]


def register_opts(group):
    CONF.register_opts(paypal_opts, group)
