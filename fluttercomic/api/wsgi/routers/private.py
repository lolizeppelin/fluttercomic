# -*- coding:utf-8 -*-
from simpleutil.utils import singleton
from simpleservice.wsgi import router
from simpleservice.wsgi.middleware import controller_return_response

from fluttercomic import common
from fluttercomic.api.wsgi.controllers import comic
from fluttercomic.api.wsgi.controllers import manager
from fluttercomic.api.wsgi.controllers import user


@singleton.singleton
class UserPrivateRouters(router.ComposableRouter):

    """必须经过认证拦截器的路由"""

    def add_routes(self, mapper):
        user_controller = controller_return_response(user.UserRequest(), user.FAULT_MAP)
        collection = mapper.collection(collection_name='users',
                                       resource_name='user',
                                       controller=user_controller,
                                       path_prefix='/%s/private' % common.NAME,
                                       member_prefix='/{uid}',
                                       collection_actions=['index'],
                                       member_actions=['show', 'update', 'delete'])
        collection.member.link('books', method='GET')
        collection.member.link('order', method='PUT')


@singleton.singleton
class ComicPrivateRouters(router.ComposableRouter):

    def add_routes(self, mapper):

        comic_controller = controller_return_response(comic.ComicRequest(), comic.FAULT_MAP)

        mapper.collection(collection_name='comics',
                          resource_name='comic',
                          controller=comic_controller,
                          path_prefix='/%s/private' % common.NAME,
                          member_prefix='/{cid}',
                          collection_actions=['index', 'create'],
                          member_actions=['show', 'update', 'delete'])
        # collection.member.link('chapters', method='POST')

        # self._add_resource(mapper, comic_controller,
        #                    path='/%s/private/comic/{cid}/user/{uid}' % common.NAME,
        #                    put_action='mark')
        # self._add_resource(mapper, comic_controller,
        #                    path='/%s/private/comic/{cid}/user/{uid}' % common.NAME,
        #                    delete_action='unmark')
        # self._add_resource(mapper, comic_controller,
        #                    path='/%s/private/comic/{cid}/chapters/{chapter}' % common.NAME,
        #                    post_action='new')
        # self._add_resource(mapper, comic_controller,
        #                    path='/%s/private/comic/{cid}/chapters/{chapter}' % common.NAME,
        #                    patch_action='finished')
        #
        # self._add_resource(mapper, comic_controller,
        #                    path='/%s/private/comic/{cid}/chapters/{chapter}' % common.NAME,
        #                    delete_action='unfinish')
        # self._add_resource(mapper, comic_controller,
        #                    path='/%s/private/comic/{cid}/chapter/{chapter}/user/{uid}' % common.NAME,
        #                    post_action='buy')

        mapper.connect('mark_comics',
                       path='/%s/private/comic/{cid}/user/{uid}' % common.NAME,
                       controller=comic_controller, action='mark',
                       conditions=dict(method=['PUT']))

        mapper.connect('unmark_comics',
                       path='/%s/private/comic/{cid}/user/{uid}' % common.NAME,
                       controller=comic_controller, action='unmark',
                       conditions=dict(method=['DELETE']))

        mapper.connect('buy_chapters',
                       path='/%s/private/comic/{cid}/chapter/{chapter}/user/{uid}' % common.NAME,
                       controller=comic_controller, action='buy',
                       conditions=dict(method=['POST']))

        mapper.connect('new_chapters',
                       path='/%s/private/comic/{cid}/chapters/{chapter}' % common.NAME,
                       controller=comic_controller, action='new',
                       conditions=dict(method=['POST']))

        mapper.connect('new_chapters',
                       path='/%s/private/comic/{cid}/chapters/{chapter}' % common.NAME,
                       controller=comic_controller, action='finished',
                       conditions=dict(method=['PATCH']))

        mapper.connect('new_chapters',
                       path='/%s/private/comic/{cid}/chapters/{chapter}' % common.NAME,
                       controller=comic_controller, action='unfinish',
                       conditions=dict(method=['DELETE']))


@singleton.singleton
class ManagerPrivateRouters(router.ComposableRouter):

    def add_routes(self, mapper):

        manager_controller = controller_return_response(manager.ManagerRequest(), manager.FAULT_MAP)
        collection = mapper.collection(collection_name='managers',
                                       resource_name='manager',
                                       controller=manager_controller,
                                       path_prefix='/%s/private' % common.NAME,
                                       member_prefix='/{mid}',
                                       collection_actions=['index', 'create'],
                                       member_actions=['show', 'update', 'delete'])
        collection.member.link('loginout', method='POST')


class Routers(router.RoutersBase):

    def append_routers(self, mapper, routers=None):

        ComicPrivateRouters(mapper)
        UserPrivateRouters(mapper)
        ManagerPrivateRouters(mapper)
