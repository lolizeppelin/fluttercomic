from simpleutil.utils.zlibutils.excluder import Excluder

SHELLZIPEXCLUDES = ['**db']
SHELTAREXCLUDE = ['*.db']


class ComicExcluder(Excluder):

    def __call__(self, compretype, shell=False):
        """find excluder function"""
        if not shell:
            raise TypeError('Just for shell extract')
        if compretype == 'zip':
            return ComicExcluder.unzip
        elif compretype == 'gz':
            return ComicExcluder.untar
        else:
            raise NotImplementedError('Can not extract %s file' % compretype)

    @staticmethod
    def unzip():
        return SHELLZIPEXCLUDES

    @staticmethod
    def untar():
        return SHELTAREXCLUDE