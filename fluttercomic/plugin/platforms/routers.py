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
            mod = 'fluttercomic.plugin.wsgi.platforms.%s.controller' % platform.lower()
            module = importutils.import_module(mod)
            cls = getattr(module, '%sRequest' % platform.capitalize())
            controller = controller_return_response(cls(), module.FAULT_MAP)

            self._add_resource(mapper, controller,
                               path='/%s/orders/platforms/%s' % (common.NAME, platform.lower()),
                               get_action='html')

            self._add_resource(mapper, controller,
                               path='/%s/orders/platforms/%s' % (common.NAME, platform.lower()),
                               post_action='new')

            self._add_resource(mapper, controller,
                               path='/%s/orders/callback/%s/{oid}' % (common.NAME, platform.lower()),
                               post_action='esure')

            self._add_resource(mapper, controller,
                               path='/%s/orders/gifts/%s' % (common.NAME, platform.lower()),
                               post_action='gift')
