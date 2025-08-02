# -*- coding: utf-8 -*-

import base64
import werkzeug

from odoo import http
from odoo.http import request


class PaypalResponses(http.Controller):

    @http.route('/get/paypal/responses', auth='public')
    def get_paypal_responses(self, **post):
        if len(post) == 1 and post.get('token'):
            redirect_url = base64.decodestring(request.session['sale_order_url'])
            return werkzeug.utils.redirect(redirect_url)

        if post.get('PayerID') and post.get('paymentId'):
            tx = request.env['payment.transaction'].browse(int(request.session['transaction_id']))
            redirect_url = base64.decodestring(request.session['sale_order_url'])
            tx.sudo().execute_paypal_payment(post['PayerID'], post['paymentId'])
            return werkzeug.utils.redirect(redirect_url)
