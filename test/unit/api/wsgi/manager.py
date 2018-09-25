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


a = r'D:\backup\etc\goperation\goperation.conf'
b = r'D:\backup\etc\goperation\gcenter.conf'

configure([a, b])

wsgi_url = '172.31.0.110'
wsgi_port = 7999

from requests import session

httpclient = ManagerClient(wsgi_url, wsgi_port, timeout=30, session=session())

client = FlutterComicClient(httpclient)


def users_index():
    try:
        r = client.users_index('KJGLAG')
    except AfterRequestError as e:
        print e.resone
    else:
        print r

def manager_show(mid, token):
    try:
        r = client.manager_show(mid, token)
    except AfterRequestError as e:
        print e.resone
    else:
        print r


def manager_login():
    try:
        r = client.manager_login(mid='admin', body={'passwd': '111111'})
    except AfterRequestError as e:
        print e.resone
    else:
        data = r['data'][0]
        token = data['token']
        print token
        mid = data['mid']
        print 'login success'
        # manager_show(mid, token)



# users_index()
manager_login()
