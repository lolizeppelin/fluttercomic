from pyquery import PyQuery as pq


class shenshi(object):


    def __index__(self):
        self.chapters = []

    def request(self, action, url):
        return ''


    def get_images(self, url):
        doc = pq(self.request('chapters', url))


    def get_chapters(self, url, next=False):

        doc = pq(self.request('chapters', url))
        chapters = []

        for li in doc('.gallary_item'):
            chapter_link = li[0][0]
            chapter_info = li[1][0][-1]
            chapters.append(dict(url=chapter_link.get('href'), index=chapter_info.text))
        if next:
            url = doc('.paginator')[0][-1][0].get('href')
            self.get_chapters(url, True)