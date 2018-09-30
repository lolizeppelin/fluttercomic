import os
import subprocess
from simpleutil import systemutils
from simpleutil.utils import zlibutils

from fluttercomic import common


CONVERT = systemutils.find_executable('fluttercomic-resize')

def convert_cover(target, rename='main.jpg', size='1600x1200', maxsize=250000, logfile=None):
    args = [CONVERT, '--target', target, '-s', size, '-m', str(maxsize), '-r', rename, '-o', '15']
    if logfile:
        args.extend(['--log-file', logfile, '--loglevel', 'info'])
    sub = subprocess.Popen(args, close_fds=True, executable=CONVERT)
    systemutils.subwait(sub)


def convert_chapter(dst, key, size='1200x900', maxsize=250000, logfile=None):
    # call convert
    args = [CONVERT, '--target', dst, '-s', size, '-m', str(maxsize), '-k', key, '-o', '3600']
    if logfile:
        args.extend(['--log-file', logfile, '--loglevel', 'info'])
    sub = subprocess.Popen(args, close_fds=True, executable=CONVERT)
    systemutils.subwait(sub)
