import os
import subprocess
from simpleutil import systemutils
from simpleutil.utils import zlibutils

from fluttercomic import common


CONVERT = systemutils.find_executable('fluttercomic-resize')

def convert_cover(target, rename='main.jpg', size='1200x900', maxsize=250000):
    command = [CONVERT, '--target', target, '-s', size, '-m', str(maxsize), '-r', rename, '-t', '15']
    command = ' '.join(command)
    sub = subprocess.Popen(command, close_fds=True, executable=CONVERT)
    sub.wait()


def convert_chapter(src, dst, key, size='800x600', maxsize=250000):
    # call convert
    command = [CONVERT, '--target', dst, '-s', size, '-m', str(maxsize), '-k', key, '-t', '3600']
    command = ' '.join(command)
    sub = subprocess.Popen(command, close_fds=True, executable=CONVERT)
    sub.wait()