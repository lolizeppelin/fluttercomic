# -*- coding:utf-8 -*-
import datetime
import time

import string
import random
import hashlib

from lxml import etree
import xmltodict


from requests import sessions
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter

from simpleutil.log import log as logging
from simpleutil.utils import jsonutils
from simpleutil.utils import encodeutils

from goperation.manager.filters.filter import AuthFilter

from fluttercomic.plugin.platforms import exceptions
from fluttercomic.plugin.platforms.base import PlatFormClient
from fluttercomic.plugin.platforms.weixin.config import NAME


LOG = logging.getLogger(__name__)

def random_string(length=16):
    rule = string.ascii_letters + string.digits
    rand_list = random.sample(rule, length)
    return ''.join(rand_list)



class WeiXinApi(PlatFormClient):

    API = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
    SANDBOXAPI = 'https://api.mch.weixin.qq.com/sandboxnew/pay/unifiedorder'

    RECHACK = ''
    SANDRECHACK = ''

    def __init__(self, conf):
        super(WeiXinApi, self).__init__(NAME, conf)

        self.api = self.SANDBOXAPI if self.sandbox else self.API
        self.recheck = self.SANDRECHACK if self.sandbox else self.RECHACK

        self.appid = conf.appId
        self.mchid = conf.mchId
        self.appname = conf.appName
        self.overtime = conf.overtime


    @staticmethod
    def format_url(params, api_key=None):
        data = [encodeutils.safe_decode('{0}={1}'.format(k, params[k])) for k in sorted(params) if params[k]]
        if api_key:
            data.append(encodeutils.safe_decode('key={0}'.format(api_key)))
        return b"&".join(data)

    @staticmethod
    def calculate_signature(params, api_key=None):
        url = WeiXinApi.format_url(params, api_key)
        return encodeutils.safe_decode(hashlib.md5(url).hexdigest().upper())


    def _unifiedorder_xml(self, money, oid, timeline, req):

        overtime = timeline + self.overtime

        data = {
            'appId': self.appid,
            'mch_id': self.mchid,
            'nonceStr': random_string(),
            'signType': 'MD5',
            'body': '%s-充值' % encodeutils.safe_decode(self.appname),
            'time_start': datetime.datetime.utcfromtimestamp(timeline).strftime('%Y%m%d%H%M%S'),
            'time_expire': datetime.datetime.utcfromtimestamp(overtime).strftime('%Y%m%d%H%M%S'),
            'out_trade_no': encodeutils.safe_decode(oid),
            'fee_type': self.currency,
            'total_fee': money*100,
            'spbill_create_ip': AuthFilter.client_addr(req),
            'notify_url': req.path_url + '/%d' % oid,
            'trade_type': 'APP',
        }
        sign = WeiXinApi.calculate_signature(data)
        data['sign'] = sign

        root = etree.Element('xml')
        root.text = '\n'
        for key in data:
            em = etree.Element(key)
            em.text = data[key]
            em.tail = '\n'
            root.append(em)
        return etree.tostring(root)

    @staticmethod
    def _decrypt_xml_to_dict(data):
        data_dict = xmltodict.parse(encodeutils.safe_decode(data))['xml']
        sign = data_dict.pop('sign')
        if sign != WeiXinApi.calculate_signature(data):
            raise
        return data_dict


    def payment(self, money, oid, timeline, req):
        money = int(money*self.roe)
        data = self._unifiedorder_xml(money, oid, timeline, req)
        resp = self.session.post(self.API, data=data,
                                 headers={"Content-Type": "application/xml"}, timeout=10)
        result = WeiXinApi._decrypt_xml_to_dict(resp.text)
        if result.get('return_code') != 'SUCCESS':
            LOG.error('Create WeiXin request payment api fail: %s' % result.get('return_msg'))
            raise exceptions.CreateOrderError('Create WeiXin order fail')
        if result.get('result_code') != 'SUCCESS':
            LOG.error('Create WeiXin order fail')
            raise exceptions.CreateOrderError('Create WeiXin order fail')
        return result['prepay_id']

    def esure(self, data, order):
        data = WeiXinApi._decrypt_xml_to_dict(data)
        if data.get('return_code') != 'SUCCESS':
            LOG.error('Create WeiXin request payment api fail: %s' % data.get('return_msg'))
            raise
        if data.get('result_code') != 'SUCCESS':
            LOG.error('Create WeiXin create payment fail')
            raise
        if data['out_trade_no'] != str(order.oid):
            raise
        money = int(data['total_fee'])
        if money != order.money*100:
            raise
        # return data