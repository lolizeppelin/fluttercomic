# -*- coding:utf-8 -*-
from fluttercomic import common
from fluttercomic.api.wsgi import comic
from fluttercomic.api.wsgi import user
from simpleservice.wsgi import router

COLLECTION_ACTIONS = ['index', 'create']
MEMBER_ACTIONS = ['show', 'update', 'delete']


class Routers(router.RoutersBase):

    """不需要经过认证拦截器的路由"""

    resource_name = 'fluttercomicpub'

    def append_routers(self, mapper, routers=None):

        user_controller = user.UserRequest()

        collection = mapper.collection(collection_name='users',
                                       resource_name='fcusers_pub',
                                       controller=user_controller,
                                       path_prefix='/%s/public' % common.NAME,
                                       member_prefix='/{uid}',
                                       collection_actions=['create'],
                                       member_actions=[])
        collection.member.link('login', method='PUT')


        comic_controller = comic.ComicRequest()
        mapper.collection(collection_name='comics',
                          resource_name='fcomic_pub',
                          controller=comic_controller,
                          path_prefix='/%s/public' % common.NAME,
                          member_prefix='/{cid}',
                          collection_actions=['index'],
                          member_actions=['show'])
