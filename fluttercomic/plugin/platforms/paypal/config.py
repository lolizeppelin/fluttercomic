from simpleutil.config import cfg

from fluttercomic import common

from fluttercomic.plugin.platforms import config

CONF = cfg.CONF

NAME = 'paypal'


group = cfg.OptGroup(name='%s.%s' % (common.NAME, NAME), title='Fluttercomic Pay platform paypal')

paypal_opts = [
    cfg.StrOpt('clientID',
               help='paypal clientID'),
    cfg.StrOpt('secret',
               secret=True,
               help='paypal secret'),
]


def register_opts(group):
    CONF.register_opts(paypal_opts + config.platform_opts, group)
    config.register_platform(name=NAME,
                             choices=list(set(CONF[group.name].choices)),
                             scale=CONF[group.name].scale,
                             currency=CONF[group.name].currency)

