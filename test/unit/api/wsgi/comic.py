# -*- coding:utf-8 -*-
import time
import os
import logging as defalut_logging
from simpleutil.log import log as logging
from simpleutil.config import cfg
from simpleutil.utils import digestutils

from simpleservice.plugin.exceptions import HttpRequestError
from simpleservice.plugin.exceptions import BeforeRequestError
from simpleservice.plugin.exceptions import AfterRequestError

from goperation.api.client import ManagerClient

from fluttercomic.api.client import FlutterComicClient


CONF = cfg.CONF
logging.register_options(CONF)
logging.register_options(CONF)

def configure(config_files):
    group = cfg.OptGroup(name='test', title='group for test')
    args = None
    CONF(args=args,
         project=group.name,
         default_config_files=config_files)
    CONF.register_group(group)
    # set base confi
    # reg base opts
    # set log config
    logging.setup(CONF, group.name)
    defalut_logging.captureWarnings(True)


basepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../etc'))

configs = [
    os.path.join(basepath, 'goperation.conf'),
    os.path.join(basepath, 'gcenter.conf')
]

configure(configs)

wsgi_url = '192.168.191.10'
wsgi_port = 7999
from requests import session

httpclient = ManagerClient(wsgi_url, wsgi_port, timeout=30, session=session())

client = FlutterComicClient(httpclient)


def comics_index():
    try:
        r = client.comics_index()
    except AfterRequestError as e:
        print e.resone
    else:
        print r


def comics_show(cid):
    try:
        r = client.comic_show(cid)
    except AfterRequestError as e:
        print e.resone
    else:
        print r


def comics_show_private():
    try:
        r = client.comic_show_private(cid=1, token='')
    except AfterRequestError as e:
        print e.resone
    else:
        print r


# comics_index()
comics_show(1)
# comics_show_private()
