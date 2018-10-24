HTMLTEMPLATE = '''
<script src="https://www.paypalobjects.com/api/checkout.js"></script>

<div id="paypal-button"></div>

<script>
    paypal.Button.render({
        style: {size: 'responsive', 'label': 'buynow', 'size': 'responsive'},
        env: 'sandbox',
        payment: function(data, actions) {
            return actions.request.post('/fluttercomic/orders/platform/paypal',
                { 'money': %(money)d, 'uid': %(uid)d, 'oid': %(oid)d, 'cid': %(cid)d, 'chapter': %(chapter)d })
                .then(function(res) {
                    return res.data[0].paypal.paymentID;
                });
        },
        onAuthorize: function(data, actions) {
            return actions.request.post('/fluttercomic/orders/callback/paypal/%(oid)d',
                                        {
                                            paypal: {
                                                paymentID: data.paymentID,
                                                payerID:   data.payerID
                                            },
                                            oid: %(oid)d
                                        }
            )
                .then(function(res) {
                    // 3. Show the buyer a confirmation message.
                });
        }
    }, '#paypal-button');
</script>
'''

print HTMLTEMPLATE % {'uid': 0, 'cid': 0, 'chapter': 0, 'money': 0, 'oid': 0}