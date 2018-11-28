from simpleservice.plugin.exceptions import ServerExecuteRequestError

from goperation.manager import common
from goperation.api.client import GopHttpClientApi


class FlutterComicClient(GopHttpClientApi):

    users_path = '/fluttercomic/%s/users'
    user_path = '/fluttercomic/%s/users/%s'
    user_path_ex = '/fluttercomic/%s/users/%s/%s'

    managers_path = '/fluttercomic/%s/managers'
    manager_path = '/fluttercomic/%s/managers/%s'
    manager_path_ex = '/fluttercomic/%s/managers/%s/%s'

    comics_path = '/fluttercomic/%s/comics'
    comic_path = '/fluttercomic/%s/comics/%s'

    mark_path = '/fluttercomic/private/comic/%s/user/%s'
    buy_path = '/fluttercomic/private/comic/%s/chapter/%s/user/%s'
    chapter_path = '/fluttercomic/private/comic/%s/chapters/%s'

    platforms_path = '/fluttercomic/platforms'

    PRIVATE = 'private'
    PUBLIC = 'public'

    PUBLICVERSION = 'n1.0'

    # -----------users api-----------------
    def users_index(self, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.get(action=self.users_path % self.PRIVATE, headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='list fluttercomic users fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def users_create(self, body=None):
        resp, results = self.retryable_post(action=self.users_path % self.PUBLIC,
                                            body=body, version=self.PUBLICVERSION)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='create fluttercomic user fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_show(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.get(action=self.user_path % (self.PRIVATE, str(uid)), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='show fluttercomic user fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_update(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.put(action=self.user_path % (self.PRIVATE, uid), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='update fluttercomic user fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_delete(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.delete(action=self.user_path % (self.PRIVATE, uid), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='delete fluttercomic user fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_books(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.get(action=self.user_path_ex % (self.PRIVATE, uid, 'books'), headers=headers)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='get fluttercomic user books fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_order(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.put(action=self.user_path_ex % (self.PRIVATE, uid, 'order'), headers=headers)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic user create order fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_orders(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.get(action=self.user_path_ex % (self.PRIVATE, uid, 'orders'), headers=headers)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic get user orders fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results


    def user_paylogs(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.put(action=self.user_path_ex % (self.PRIVATE, uid, 'paylogs'), headers=headers)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic user create order fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_login(self, uid, body=None):
        headers = { common.FERNETHEAD: 'yes'}
        resp, results = self.put(action=self.user_path_ex % (self.PUBLIC, uid, 'login'), headers=headers,
                                 body=body, version=self.PUBLICVERSION)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic user login fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    # ----------managers api---------------
    def managers_index(self, token, body=None):
        headers = {common.TOKENNAME: token}
        resp, results = self.get(action=self.managers_path % self.PRIVATE, headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='list fluttercomic manager fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def manager_show(self, mid, token, body=None):
        headers = {common.TOKENNAME: token}
        resp, results = self.get(action=self.manager_path % (self.PRIVATE, str(mid)), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='show fluttercomic manager fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def manager_update(self, mid, token, body=None):
        headers = {common.TOKENNAME: token}
        resp, results = self.put(action=self.manager_path % (self.PRIVATE, str(mid)), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='update fluttercomic manager fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def manager_delete(self, mid, token, body=None):
        headers = {common.TOKENNAME: token}
        resp, results = self.delete(action=self.manager_path % (self.PRIVATE, str(mid)), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='delete fluttercomic manager fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def manager_login(self, mid, body=None):
        resp, results = self.post(action=self.manager_path_ex % (self.PUBLIC, str(mid), 'login'),
                                  body=body, version=self.PUBLICVERSION)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic manager login fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    # -----------comic api-----------------
    def comics_index(self, body=None):
        resp, results = self.get(action=self.comics_path % self.PUBLIC, body=body, version=self.PUBLICVERSION)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='list fluttercomic comics fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comics_create(self, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.retryable_post(action=self.comics_path % self.PRIVATE, headers=headers)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='create fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_show(self, cid, body=None):
        resp, results = self.get(action=self.comic_path % (self.PUBLIC, cid), body=body, version=self.PUBLICVERSION)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='show fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_show_private(self, cid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.get(action=self.comic_path % (self.PRIVATE, cid), headers=headers)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='show fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_update(self, cid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.put(action=self.comic_path % (self.PRIVATE, cid), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='update fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_delete(self, cid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.delete(action=self.comic_path % (self.PRIVATE, cid), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='update fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_mark(self, cid, uid, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.put(action=self.mark_path % (self.PRIVATE, cid, uid),
                                 headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='mark fluttercomic comic chapter fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_unmark(self, cid, uid, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.delete(action=self.mark_path % (self.PRIVATE, cid, uid),
                                    headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='unmark fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    # ----------chapter api ---------------
    def chapter_buy(self, cid, chapter, uid, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.post(action=self.buy_path % (self.PRIVATE, cid, chapter, uid),
                                  headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='buy fluttercomic comic chapter fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def chapter_create(self, cid, chapter, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: 'yes'}
        resp, results = self.retryable_post(action=self.chapter_path % (self.PRIVATE, cid, chapter),
                                            headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic comic create chapter fail:%d' %
                                                    results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results
