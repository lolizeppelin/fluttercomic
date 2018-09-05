from simpleservice.plugin.exceptions import ServerExecuteRequestError

from goperation.manager import common
from goperation.api.client import GopHttpClientApi


class FlutterComicClient(GopHttpClientApi):

    users_path = '/fluttercomic/%s/users'
    user_path = '/fluttercomic/%s/users/%s'
    user_path_ex = '/fluttercomic/%s/users/%s/%s'

    comics_path = '/fluttercomic/%s/comics'
    comic_path = '/fluttercomic/%s/comics/%s'

    mark_path = '/fluttercomic/private/comic/%s/user/%s'
    buy_path = '/fluttercomic/private/comic/%s/chapter/%s/user/%s'
    chapter_path = '/fluttercomic/private/comic/%s/chapters/%s'

    PRIVATE = 'private'
    PUBLIC = 'public'

    # -----------users api-----------------
    def users_index(self, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.get(action=self.users_path % self.PRIVATE, headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='list fluttercomic users fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def users_create(self, body=None):
        resp, results = self.retryable_post(action=self.users_path % self.PUBLIC,
                                            body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='create fluttercomic user fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_show(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.get(action=self.user_path % (self.PRIVATE, uid), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='show fluttercomic user fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_update(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.put(action=self.user_path % (self.PRIVATE, uid), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='update fluttercomic user fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_delete(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.delete(action=self.user_path % (self.PRIVATE, uid), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='delete fluttercomic user fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_books(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.get(action=self.user_path_ex % (self.PRIVATE, uid, 'books'), headers=headers,
                                 body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='get fluttercomic user books fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_order(self, uid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.put(action=self.user_path_ex % (self.PRIVATE, uid, 'order'), headers=headers,
                                 body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic user create order fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def user_login(self, uid, body=None):
        resp, results = self.put(action=self.user_path_ex % (self.PUBLIC, uid, 'login'), body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic user login fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    # -----------comic api-----------------
    def comics_index(self, body=None):
        resp, results = self.get(action=self.comics_path % self.PUBLIC, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='list fluttercomic comics fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comics_create(self, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.retryable_post(action=self.comics_path % self.PRIVATE, headers=headers,
                                            body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='create fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_show(self, cid, body=None):
        resp, results = self.get(action=self.comic_path % (self.PUBLIC, cid), body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='show fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_show_private(self, cid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.get(action=self.comic_path % (self.PRIVATE, cid), headers=headers,
                                 body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='show fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_update(self, cid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.put(action=self.comic_path % (self.PRIVATE, cid), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='update fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_delete(self, cid, token, body=None):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.delete(action=self.comic_path % (self.PRIVATE, cid), headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='update fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_mark(self, cid, uid, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.put(action=self.mark_path % (self.PRIVATE, cid, uid),
                                 headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='mark fluttercomic comic chapter fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def comic_unmark(self, cid, uid, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.delete(action=self.mark_path % (self.PRIVATE, cid, uid),
                                    headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='unmark fluttercomic comic fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    # ----------chapter api ---------------
    def chapter_buy(self, cid, chapter, uid, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.post(action=self.buy_path % (self.PRIVATE, cid, chapter, uid),
                                  headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='buy fluttercomic comic chapter fail:%d' % results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def chapter_create(self, cid, chapter, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.retryable_post(action=self.chapter_path % (self.PRIVATE, cid, chapter),
                                            headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic comic create chapter fail:%d' %
                                                    results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def chapter_finsh(self, cid, chapter, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.patch(action=self.chapter_path % (self.PRIVATE, cid, chapter),
                                   headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic comic create finish fail:%d' %
                                                    results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    def chapter_unfinsh(self, cid, chapter, token, body):
        headers = {common.TOKENNAME: token, common.FERNETHEAD: True}
        resp, results = self.delete(action=self.chapter_path % (self.PRIVATE, cid, chapter),
                                    headers=headers, body=body)
        if results['resultcode'] != common.RESULT_SUCCESS:
            raise ServerExecuteRequestError(message='fluttercomic comic create unfinish fail:%d' %
                                                    results['resultcode'],
                                            code=resp.status_code,
                                            resone=results['result'])
        return results

    # ----------manager api ---------------