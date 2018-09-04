# -*- coding:utf-8 -*-
from fluttercomic import common
from fluttercomic.api.wsgi import comic
from fluttercomic.api.wsgi import user
from simpleservice.wsgi import router

COLLECTION_ACTIONS = ['index', 'create']
MEMBER_ACTIONS = ['show', 'update', 'delete']


class Routers(router.RoutersBase):

    """必须经过认证拦截器的路由"""

    resource_name = 'fluttercomicpri'



    def append_routers(self, mapper, routers=None):

        user_controller = user.UserRequest()

        collection = mapper.collection(collection_name='users',
                                       resource_name='fcusers_pri',
                                       controller=user_controller,
                                       path_prefix='/%s/private' % common.NAME,
                                       member_prefix='/{uid}',
                                       collection_actions=['index'],
                                       member_actions=['show', 'update', 'delete'])
        collection.member.link('books', method='GET')
        collection.member.link('order', method='PUT')


        comic_controller = comic.ComicRequest()
        mapper.collection(collection_name='comics',
                          resource_name='fcomics_pri',
                          controller=comic_controller,
                          path_prefix='/%s/private' % common.NAME,
                          member_prefix='/{cid}',
                          collection_actions=COLLECTION_ACTIONS,
                          member_actions=MEMBER_ACTIONS)
        # collection.member.link('chapters', method='POST')

        self._add_resource(mapper, comic_controller,
                           path='/%s/comic/{cid}/chapter/{chapter}/user/{uid}' % common.NAME,
                           post_action='buy')

        self._add_resource(mapper, user_controller,
                           path='/%s/comic/{cid}/user/{uid}' % common.NAME,
                           put_action='mark')

        self._add_resource(mapper, user_controller,
                           path='/%s/comic/{cid}/user/{uid}' % common.NAME,
                           delete_action='unmark')

        self._add_resource(mapper, user_controller,
                           path='/%s/comic/{cid}/chapters/{chapter}' % common.NAME,
                           post_action='new')

        self._add_resource(mapper, user_controller,
                           path='/%s/comic/{cid}/chapters/{chapter}' % common.NAME,
                           patch_action='finished')

        self._add_resource(mapper, user_controller,
                           path='/%s/comic/{cid}/chapters/{chapter}' % common.NAME,
                           delete_action='unfinish')