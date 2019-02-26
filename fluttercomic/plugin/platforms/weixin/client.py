# -*- coding:utf-8 -*-
import datetime
import time

import string
import random
import hashlib

from lxml import etree
import xmltodict

import requests

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


    API = 'https://api.mch.weixin.qq.com'
    SANDBOXAPI = 'https://api.mch.weixin.qq.com/sandboxnew'

    def __init__(self, conf):
        super(WeiXinApi, self).__init__(NAME, conf)

        self.api = self.SANDBOXAPI if self.sandbox else self.API

        self.appid = conf.appId
        self.secret = conf.secret
        self.mchid = conf.mchId
        self.appname = conf.appName
        self.overtime = conf.overtime

    @property
    def success(self):
        return '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>'

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

    @staticmethod
    def dict_to_xml_string(data):
        root = etree.Element('xml')
        root.text = '\n'
        for key in data:
            em = etree.Element(key)
            em.text = data[key]
            em.tail = '\n'
            root.append(em)
        return etree.tostring(root)

    @staticmethod
    def decrypt_xml_to_dict(buf):
        return xmltodict.parse(encodeutils.safe_decode(buf))['xml']

    @property
    def sandbox_sign(self):
        data = {'mch_id': self.mchid, 'nonce_str': random_string(), 'signType': 'MD5'}
        data['sign'] = WeiXinApi.calculate_signature(data, self.secret)
        url = WeiXinApi.SANDBOXAPI + '/pay/getsignkey'
        resp = self.session.post(url, data=WeiXinApi.dict_to_xml_string(data),
                                 headers={"Content-Type": "application/xml"}, timeout=3)
        data = WeiXinApi.decrypt_xml_to_dict(resp.text)
        if data.get('return_code') != 'SUCCESS':
            LOG.error('Get WeiXin sandbox sign request fail: %s' % data.get('return_msg'))
            raise exceptions.CreateOrderError('Get WeiXin sandbox sign fail')
        if data.get('mch_id') != self.mchid:
            raise exceptions.CreateOrderError('Get WeiXin sandbox sign find mch id not the same')
        return data['sandbox_signkey']

    def _unifiedorder_xml(self, money, oid, timeline, req):

        overtime = timeline + self.overtime
        _random_str = random_string()

        data = {
            'appId': self.appid,
            'mch_id': self.mchid,
            'nonceStr': _random_str,
            'signType': 'MD5',
            'body': '%s-充值' % encodeutils.safe_decode(self.appname),
            'time_start': datetime.datetime.utcfromtimestamp(timeline).strftime('%Y%m%d%H%M%S'),
            'time_expire': datetime.datetime.utcfromtimestamp(overtime).strftime('%Y%m%d%H%M%S'),
            'out_trade_no': str(oid),
            'fee_type': self.currency,
            'total_fee': str(money*100),
            'spbill_create_ip': AuthFilter.client_addr(req),
            'notify_url': req.path_url + '/%d' % oid,
            'trade_type': 'APP',
        }
        data['sign'] = self.sandbox_sign if self.sandbox else WeiXinApi.calculate_signature(data, self.secret)
        return self._dict_to_xml_string(data), _random_str

    def _orderquery_xml(self, oid):
        data = {
            'appId': self.appid,
            'mch_id': self.mchid,
            'nonceStr': random_string(),
            'transaction_id': str(oid),
        }
        return self._dict_to_xml_string(data)

    def _check_sign(self, data):
        if not self.sandbox:
            sign = data.pop('sign', None)
            if not sign or sign != WeiXinApi.calculate_signature(data, self.secret):
                raise exceptions.OrderError('Sign not the same')

    def esure_notify(self, data, order):
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug(data)
        data = WeiXinApi.decrypt_xml_to_dict(data)
        self._check_sign(data)
        if data.get('return_code') != 'SUCCESS':
            LOG.error('Esure WeiXin order api request fail: %s' % data.get('return_msg'))
            raise exceptions.EsureOrderError('Esure WeiXin order error, request error')
        if data.get('result_code') != 'SUCCESS':
            LOG.error('Esure WeiXin order result fail')
            raise exceptions.EsureOrderError('Esure WeiXin order error, result error')
        if data['out_trade_no'] != str(order.oid):
            LOG.error('Esure WeiXin order error, oid not the same')
            raise exceptions.EsureOrderError('Esure WeiXin order error, oid not the same')
        money = int(data['total_fee'])
        if money != order.money*100:
            LOG.warning('Money not the same! order %d, use value from order' % order.oid)
        try:
            prepay_id = jsonutils.loads_as_bytes(order.ext)['prepay_id'] if order.ext else None
        except Exception as e:
            LOG.error('Get prepay_id from order fail, %s' % e.__class__.__name__)
            prepay_id = None
        return data['transaction_id'], {'prepay_id': prepay_id}

    def payment(self, money, oid, timeline, req):
        money = int(money*self.roe)
        data, random_str = self._unifiedorder_xml(money, oid, timeline, req)
        url = self.api + '/pay/unifiedorder'
        resp = self.session.post(url, data=data,
                                 headers={"Content-Type": "application/xml"}, timeout=10)
        result = WeiXinApi.decrypt_xml_to_dict(resp.text)
        if result.get('return_code') != 'SUCCESS':
            LOG.error('Create WeiXin request payment api fail: %s' % result.get('return_msg'))
            raise exceptions.CreateOrderError('Create WeiXin order fail')
        if result.get('result_code') != 'SUCCESS':
            LOG.error('Create WeiXin order fail')
            raise exceptions.CreateOrderError('Create WeiXin order fail')
        self._check_sign(result)
        return result['prepay_id'], result['sign'], random_str

    def esure_order(self, order):
        url = self.api + '/pay/orderquery'
        resp = self.session.get(url, data=self._orderquery_xml(order.oid),
                                headers={"Content-Type": "application/xml"}, timeout=10)
        return self.esure_notify(resp.text, order)

