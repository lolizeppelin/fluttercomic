from simpleutil.config import cfg

from fluttercomic import common

from fluttercomic.plugin.platforms import config

CONF = cfg.CONF

NAME = 'ipay'


group = cfg.OptGroup(name='%s.%s' % (common.NAME, NAME), title='Fluttercomic Pay platform ipay')

ipay_opts = [
    cfg.StrOpt('appId',
               help='ipay appId'),
    cfg.StrOpt('appUid',
               help='ipay app userid'),
    cfg.IntOpt('waresId',
               help='ipay waresId'),
    cfg.StrOpt('signtype',
               default='RSA',
               choices=['RSA'],
               help='ipay signtype appId'),
    cfg.StrOpt('rsa_private',
               default='/etc/goperation/endpoints/platforms/ipay_private.key',
               help='ipay signtype rsa private key file'),
    cfg.StrOpt('rsa_public',
               default='/etc/goperation/endpoints/platforms/ipay_public.key',
               help='ipay signtype rsa public key file'),
    cfg.UrlOpt('url_sucess',
               help='ipay pay success request url'
               ),
    cfg.UrlOpt('url_fail',
               help='ipay pay fail request url'
               ),
]


def register_opts(group):
    CONF.register_opts(ipay_opts + config.platform_opts, group)
    config.register_platform(name=NAME,
                             choices=list(set(CONF[group.name].choices)),
                             scale=CONF[group.name].scale,
                             currency=CONF[group.name].currency,
                             appId=CONF[group.name].appId,
                             )

