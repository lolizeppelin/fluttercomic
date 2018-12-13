# -*- coding: utf-8 -*-
from lxml import etree


emp = '''
<xml>
   <appid>wx2421b1c4370ec43b</appid>
   <attach>支付测试</attach>
   <body>APP支付测试</body>
   <mch_id>10000100</mch_id>
   <nonce_str>1add1a30ac87aa2db72f57a2375d8fec</nonce_str>
   <notify_url>http://wxpay.wxutil.com/pub_v2/pay/notify.v2.php</notify_url>
   <out_trade_no>1415659990</out_trade_no>
   <spbill_create_ip>14.23.150.211</spbill_create_ip>
   <total_fee>1</total_fee>
   <trade_type>APP</trade_type>
   <sign>0CB01533B8C1EF103065174F50BCA001</sign>
</xml>
'''


root = etree.Element('xml')
root.text = '\n'


em = etree.Element('appid')
em.text = 'lkjglaga'
em.tail = '\n'
root.append(em)


em = etree.Element('attach')
em.text = 'test attach'
em.tail = '\n'
root.append(em)


em = etree.Element('body')
em.text = 'test body'
em.tail = '\n'
root.append(em)


em = etree.Element('content')
em.text = etree.CDATA(']]]]]]]]]]]]]')
em.tail = '\n'
root.append(em)

print dir(root)

print etree.tostring(root)