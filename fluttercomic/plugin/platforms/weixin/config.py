from simpleutil.config import cfg

from fluttercomic import common

from fluttercomic.plugin.platforms import config

CONF = cfg.CONF

NAME = 'weixin'


group = cfg.OptGroup(name='%s.%s' % (common.NAME, NAME), title='Fluttercomic WeiXin platform paypal')

weixin_opts = [
    cfg.StrOpt('appId',
               help='WeiXin app Id'),
    cfg.StrOpt('appName',
               help='WeiXin app name'),
    cfg.StrOpt('mchId',
           help='WeiXin mch_id'),
    cfg.StrOpt('package',
               default='Sign=WXPay',
               help='WeiXin package value'),
    cfg.StrOpt('cert',
               default='/etc/goperation/endpoints/wexin_cert.pem',
               help='WeiXin SSL apiclient cert'),
    cfg.StrOpt('key',
               default='/etc/goperation/endpoints/wexin_key.pem',
               help='WeiXin SSL apiclient key'),
    cfg.StrOpt('overtime',
               default=300,
               help='WeiXin Order overtime, by seconds'),
]


def register_opts(group):
    CONF.register_opts(weixin_opts + config.platform_opts, group)
    config.register_platform(name=NAME,
                             choices=CONF[group.name].choices,
                             scale=CONF[group.name].scale,
                             currency=CONF[group.name].currency,
                             appId=CONF[group.name].appId,
                             partnerId=CONF[group.name].mchId,
                             package=CONF[group.name].package,
                             )

