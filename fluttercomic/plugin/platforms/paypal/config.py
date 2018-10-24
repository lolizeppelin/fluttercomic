from simpleutil.config import cfg
from simpleutil.config import types

from fluttercomic import common

CONF = cfg.CONF

NAME = '%s.paypal' % common.NAME


paypal_opts = [
    cfg.StrOpt('clientID', help='paypal clientID'),
    cfg.StrOpt('secret', help='paypal secret'),
]


def register_opts(group):
    CONF.register_opts(paypal_opts, group)
