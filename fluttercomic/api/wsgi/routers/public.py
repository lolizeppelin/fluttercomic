# -*- coding:utf-8 -*-
from simpleutil.utils import singleton
from simpleservice.wsgi import router
from simpleservice.wsgi.middleware import controller_return_response

from fluttercomic import common
from fluttercomic.api.wsgi.controllers import comic
from fluttercomic.api.wsgi.controllers import user
from fluttercomic.api.wsgi.controllers import manager


@singleton.singleton
class UserPublicRouters(router.ComposableRouter):

    def add_routes(self, mapper):

        user_controller = controller_return_response(user.UserRequest(), user.FAULT_MAP)

        collection = mapper.collection(collection_name='users',
                                       resource_name='user',
                                       controller=user_controller,
                                       path_prefix='/%s/public' % common.NAME,
                                       member_prefix='/{uid}',
                                       collection_actions=['create'],
                                       member_actions=[])
        collection.member.link('login', method='PUT')


@singleton.singleton
class ComicPublicRouters(router.ComposableRouter):

    def add_routes(self, mapper):

        comic_controller = controller_return_response(comic.ComicRequest(), comic.FAULT_MAP)
        mapper.collection(collection_name='comics',
                          resource_name='comic',
                          controller=comic_controller,
                          path_prefix='/%s/public' % common.NAME,
                          member_prefix='/{cid}',
                          collection_actions=['index'],
                          member_actions=['show'])


@singleton.singleton
class ManagerPublicRouters(router.ComposableRouter):

    def add_routes(self, mapper):

        manager_controller = controller_return_response(manager.ManagerRequest(), manager.FAULT_MAP)
        collection = mapper.collection(collection_name='managers',
                                       resource_name='manager',
                                       controller=manager_controller,
                                       path_prefix='/%s/public' % common.NAME,
                                       member_prefix='/{mid}',
                                       collection_actions=[],
                                       member_actions=[])
        collection.member.link('login', method='POST')


class Routers(router.RoutersBase):

    def append_routers(self, mapper, routers=None):

        ComicPublicRouters(mapper)
        UserPublicRouters(mapper)
        ManagerPublicRouters(mapper)
