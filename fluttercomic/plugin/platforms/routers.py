from simpleutil.config import cfg
from simpleutil.utils import importutils

from simpleservice.wsgi import router
from simpleservice.wsgi.middleware import controller_return_response

from fluttercomic import common

CONF = cfg.CONF


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
                               path='/%s/orders/gifts/%s' % (common.NAME, platform.lower()),
                               post_action='gift')
