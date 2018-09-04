from simpleutil.config import cfg
from simpleutil.utils import importutils

from simpleservice.wsgi import router
from simpleservice.wsgi.middleware import controller_return_response

from fluttercomic import common
from fluttercomic.plugin.wsgi.platforms.config import register_opts

CONF = cfg.CONF


group = CONF.find_group(common.NAME)

register_opts(group)


class Routers(router.RoutersBase):

    resource_name = 'fluttercomicplat'

    def append_routers(self, mapper, routers=None):

        conf = CONF[common.NAME]

        for platform in conf.platforms:
            module = importutils.import_module('fluttercomic.plugin.wsgi.platforms.%s' % platform.lower())
            cls = getattr(module, '%sRequest' % platform.capitalize())
            controller = controller_return_response(cls(), module.FAULT_MAP)

            self._add_resource(mapper, controller,
                               path='/%s/orders/callback/%s' % (common.NAME, platform.lower()),
                               post_action='pay')

            self._add_resource(mapper, controller,
                               path='/%s/orders/gitfs/%s' % (common.NAME, platform.lower()),
                               post_action='gift')
