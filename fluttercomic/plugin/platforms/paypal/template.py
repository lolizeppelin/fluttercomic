# -*- coding:utf-8 -*-
"""
HTMLTEMPLATE 是paypal充值页面模板
"""

HTMLTEMPLATE = '''
<script src="https://www.paypalobjects.com/api/checkout.js"></script>

<div id="paypal-button"></div>

<script>
    paypal.Button.render({
        locale: 'en_US',
        style: {size: 'responsive', 'label': 'buynow', 'size': 'responsive'},
        env: 'sandbox',
        payment: function(data, actions) {
            return actions.request.post('/fluttercomic/orders/platform/paypal',
                {'money': %(money), 'uid': %(uid), 'oid': %(oid), 'cid': %(cid), 'chapter': %(chapter)})
                .then(function(res) {
                    return res.data[0].paypal.paymentID;
                });
        },
        onAuthorize: function(data, actions) {
            return actions.request.post('/fluttercomic/orders/callback/paypal/%(oid)',
                                        {
                                            paypal: {
                                                paymentID: data.paymentID,
                                                payerID:   data.payerID
                                            },
                                            oid: %(oid)
                                        }
            )
                .then(function(res) {
                    // 3. Show the buyer a confirmation message.
                });
        }
    }, '#paypal-button');
</script>
'''


def html(oid, uid, cid, chapter, money):
    return HTMLTEMPLATE % {'oid': oid, 'uid': uid, 'money': money, 'cid': cid, 'chapter': chapter}


def translate(money):
    return money*10, 0