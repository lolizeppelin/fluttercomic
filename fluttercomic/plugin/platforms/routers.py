from simpleutil.config import cfg
from simpleutil.utils import importutils

from simpleservice.wsgi import router
from simpleservice.wsgi.middleware import controller_return_response

from fluttercomic import common

from fluttercomic.plugin.platforms.base import PlatformsRequestPublic

CONF = cfg.CONF


class Routers(router.RoutersBase):

    resource_name = 'fluttercomic_platform'

    def append_routers(self, mapper, routers=None):

        conf = CONF[common.NAME]

        controller = controller_return_response(PlatformsRequestPublic(), {})

        self._add_resource(mapper, controller,
                           path='/%s/platforms' % common.NAME,
                           get_action='platforms')


        for platform in conf.platforms:
            mod = 'fluttercomic.plugin.platforms.%s.controller' % platform.lower()
            module = importutils.import_module(mod)
            cls = getattr(module, '%sRequest' % platform.capitalize())
            ctrl_instance = cls()
            controller = controller_return_response(cls(), module.FAULT_MAP)

            self._add_resource(mapper, controller,
                               path='/%s/orders/platforms/%s' % (common.NAME, platform.lower()),
                               get_action='html')

            self._add_resource(mapper, controller,
                               path='/%s/orders/platforms/%s' % (common.NAME, platform.lower()),
                               post_action='new')

            self._add_resource(mapper, controller,
                               path='/%s/orders/platforms/%s/{oid}' % (common.NAME, platform.lower()),
                               post_action='notify')

            self._add_resource(mapper, controller,
                   path='/%s/orders/platforms/%s/{oid}' % (common.NAME, platform.lower()),
                   get_action='esure')

            ctrl_instance.extrouters(self, mapper, controller)

            # self._add_resource(mapper, controller,
            #                    path='/%s/orders/gifts/%s' % (common.NAME, platform.lower()),
            #                    post_action='gift')
