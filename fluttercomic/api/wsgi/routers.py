from simpleservice.wsgi import router
from simpleservice.wsgi.middleware import controller_return_response

from fluttercomic import common
from fluttercomic.api.wsgi import user
from fluttercomic.api.wsgi import comic
from fluttercomic.api.wsgi import order
from fluttercomic.api.wsgi import manager



COLLECTION_ACTIONS = ['index', 'create']
MEMBER_ACTIONS = ['show', 'update', 'delete']


class Routers(router.RoutersBase):

    def append_routers(self, mapper, routers=None):

        user_controller = user.UserRequest()

        collection = mapper.collection(collection_name='user',
                                       resource_name='users',
                                       controller=user_controller,
                                       path_prefix='/%s' % common.NAME,
                                       member_prefix='/{uid}',
                                       collection_actions=COLLECTION_ACTIONS,
                                       member_actions=MEMBER_ACTIONS)
        collection.member.link('login', method='PUT')
        collection.member.link('books', method='GET')
        collection.member.link('order', method='PUT')



        comic_controller = comic.ComicRequest()
        mapper.collection(collection_name='comic',
                          resource_name='comics',
                          controller=comic_controller,
                          path_prefix='/%s' % common.NAME,
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