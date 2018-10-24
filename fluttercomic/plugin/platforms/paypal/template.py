# -*- coding:utf-8 -*-
"""
HTMLTEMPLATE 是paypal充值页面模板
"""
from simpleutil.utils import encodeutils

HTMLTEMPLATE = '''
<script src="https://www.paypalobjects.com/api/checkout.js"></script>

<div id="paypal-button"></div>

<script>

    var options = {headers : { gopfernet: 'yes', 'Auth-Token': %(token)s}}

    paypal.Button.render({
        style: {'label': 'buynow', 'size': 'responsive'},
        env: 'sandbox',
        payment: function (data, actions) {
            return actions.request({
                    method: "post",
                    url: '/n1.0/fluttercomic/orders/platforms/paypal',
                    json: {'money': %(money)d, 'uid': %(uid)d, 'oid': %(oid)d, 'cid': %(cid)d, 'chapter': %(chapter)d},
                }, options)
                .then(function (res) {
                    return res.data[0].paypal.paymentID;
                });
        },
        onAuthorize: function (data, actions) {
            return actions.request({
                    method: "post",
                    url: '/n1.0/fluttercomic/orders/callback/paypal/%(oid)d',
                    json: {paypal: { paymentID: data.paymentID, payerID: data.payerID}},
                }, options)
                .then(function (res) {
                    // 3. Show the buyer a confirmation message.
                });
        }
    }, '#paypal-button');
</script>
'''


def html(oid, uid, cid, chapter, money, token):
    buf = HTMLTEMPLATE % {'oid': oid, 'uid': uid, 'money': money,
                          'cid': cid, 'chapter': chapter, 'token': token}
    return encodeutils.safe_decode(buf, 'utf-8')

def translate(money):
    return money*10, 0