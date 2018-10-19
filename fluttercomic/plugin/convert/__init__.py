import os
import subprocess
from simpleutil import systemutils
from simpleutil.utils import zlibutils

from fluttercomic import common


CONVERT = systemutils.find_executable('fluttercomic-resize')

def convert_cover(target, rename='main.webp', size='1600x1200', maxsize=250000, logfile=None):
    args = [CONVERT, '--target', target, '-s', size, '-m', str(maxsize), '-r', rename, '-o', '15']
    if logfile:
        args.extend(['--log-file', logfile, '--loglevel', 'info'])
        with open(logfile, 'w') as f:
            f.write('%s' % ' '.join(args))
    sub = subprocess.Popen(args, close_fds=True, executable=CONVERT)
    systemutils.subwait(sub)


def convert_chapter(dst, key, ext='webp', size='1200x900', maxsize=250000, logfile=None):
    # call convert
    args = [CONVERT, '--target', dst, '-s',  '-e', ext, size, '-m', str(maxsize), '-k', key, '-o', '3600']
    if logfile:
        args.extend(['--log-file', logfile, '--loglevel', 'info'])
        with open(logfile, 'w') as f:
            f.write('%s' % ' '.join(args))
    sub = subprocess.Popen(args, close_fds=True, executable=CONVERT)
    systemutils.subwait(sub)
