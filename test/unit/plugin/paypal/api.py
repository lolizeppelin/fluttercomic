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


def esure_order():
    resp, results = client.post(action='/fluttercomic/orders/platforms/paypal', body={'test': 'wtf'},
                                version='n1.0')
    print results

esure_order()
