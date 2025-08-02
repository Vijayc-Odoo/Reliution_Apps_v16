# -*- coding: utf-8 -*-
import base64
import json
import logging
import time
import werkzeug
import http.client
from six.moves import urllib

from odoo import fields, models, _
from odoo.http import request
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AcquirerPaypal(models.Model):
    _inherit = 'payment.acquirer'

    paypal_api_enabled = fields.Boolean('Use Rest API', default=False)
    paypal_api_username = fields.Char('Rest API Username', groups='base.group_user')
    paypal_api_password = fields.Char('Rest API Password', groups='base.group_user')
    paypal_api_access_token = fields.Char('Access Token', groups='base.group_user')
    paypal_api_access_token_validity = fields.Datetime('Access Token Validity', groups='base.group_user')

    def _paypal_s2s_get_access_token(self):
        res = dict.fromkeys(self.ids, False)
        parameters = werkzeug.url_encode({'grant_type': 'client_credentials'})

        for acquirer in self:
            if acquirer.state == 'enabled':
                url = 'api.paypal.com'
            else:
                url = 'api.sandbox.paypal.com'
            conn = http.client.HTTPSConnection(url)

            # add authorization header
            base64string = base64.encodestring(('%s:%s' % (
                acquirer.paypal_api_username,
                acquirer.paypal_api_password)
            ).encode()).decode().replace('\n', '')

            headers = {
                'Accept': "application/json",
                'Accept-Language': 'en_US',
                'Authorization': 'Basic %s' % base64string
            }

            conn.request("POST", "/v1/oauth2/token", parameters, headers)
            request = conn.getresponse()
            result = request.read()
            res[acquirer.id] = json.loads(result).get('access_token')
            request.close()
        return res


class TransactionPaypal(models.Model):
    _inherit = 'payment.transaction'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')

    def _get_item_list(self, order):
        res = []
        if order:
            for line in order.order_line:
                res.append({
                  "name": str(line.product_id.name),
                  "description": str(line.name),
                  "quantity": str(int(line.product_uom_qty)),
                  "price": str(line.price_unit),
                  "tax": str(line.price_tax),
                  "currency": str(order.currency_id.name)
                })
        return res

    def _paypal_s2s_send(self, values, token):
        tx = self.sudo().create(values)

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        rec_action = self.env.ref('sale.action_quotations_with_onboarding').id

        end_point = urllib.parse.urlencode({'id': tx.sale_order_id.id, 'view_type': 'form', 'model': 'sale.order', 'action': rec_action})

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % token[tx.acquirer_id.id],
        }

        data = {
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "transactions": [{
                "amount": {
                    "total": str('%.2f' % tx.amount),
                    "currency": str(tx.currency_id.name),
                    "details": {
                        "subtotal": str('%.2f' % tx.sale_order_id.amount_untaxed),
                        "tax": str('%.2f' % tx.sale_order_id.amount_tax),
                        "shipping": "0.00",
                        "handling_fee": "0.00",
                        "shipping_discount": "0.00",
                        "insurance": "0.00"
                    }
                },
                "description": str(tx.sale_order_id.name),
                "invoice_number": str('odoo_' + str(tx.sale_order_id.id) + '_' + str(tx.sale_order_id.name) + '_' + str(tx.id)),
                "payment_options": {
                    "allowed_payment_method": "INSTANT_FUNDING_SOURCE"
                },
                "soft_descriptor": str(tx.sale_order_id.name),
                "item_list": {
                    "items": self._get_item_list(tx.sale_order_id),
                }
            }],
            "note_to_payer": "Contact us for any questions on your order.",
            "redirect_urls": {
                "return_url": str(base_url) + '/get/paypal/responses',
                "cancel_url": str(base_url) + '/get/paypal/responses'
            }
        }

        data = json.dumps(data)
        if tx.acquirer_id.state == 'enabled':
            url = 'api.paypal.com'
        else:
            url = 'api.sandbox.paypal.com'

        conn = http.client.HTTPSConnection(url)
        conn.request("POST", "/v1/payments/payment", data, headers)
        res = conn.getresponse()
        response = json.loads(res.read())

        redirect_url = ''
        if response.get('state') == 'created':
            for link in response.get('links'):
                if link.get('method') == 'REDIRECT':
                    redirect_url = link.get('href')

        if redirect_url != '':
            request.session['sale_order_url'] = base64.encodestring(str(base_url + '/web#' + end_point).encode())
            request.session['transaction_id'] = tx.id
            return {
                'type': 'ir.actions.act_url',
                'target': 'self',
                'url': redirect_url,
            }

    def _paypal_s2s_validate(self, values):
        status = values.get('state')
        if status in ['approved']:
            _logger.info('Validated Paypal s2s payment for tx %s: set as done' % (self.reference))
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': values['id'],
            })
            self._set_transaction_done()
        elif status in ['pending', 'expired']:
            _logger.info('Received notification for Paypal s2s payment %s: set as pending' % (self.reference))
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': values['id'],
            })
            self._set_transaction_pending()
        else:
            error = 'Received unrecognized status for Paypal s2s payment %s: %s, set as error' % (self.reference, status)
            _logger.info(error)
            self.write({
                'date': fields.datetime.now(),
                'acquirer_reference': values['id'],
            })
            self._set_transaction_error(error)

    def _send_mail(self):
        email_template = self.env.ref('paypal_backend_payment.successfull_payment_notification')
        self.env['mail.template'].browse(email_template.id).send_mail(self.id, force_send=True)

    def execute_paypal_payment(self, payer_id, payment_id):
        self.ensure_one()
        token = self.acquirer_id._paypal_s2s_get_access_token()

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % str(token[self.acquirer_id.id]),
        }

        data = '{"payer_id": "%s"\n}' % str(payer_id)

        if self.acquirer_id.state == 'enabled':
            url = 'api.paypal.com'
        else:
            url = 'api.sandbox.paypal.com'

        conn = http.client.HTTPSConnection(url)
        conn.request("POST", '/v1/payments/payment/%s/execute' % payment_id, data, headers)
        res = conn.getresponse()
        response = json.loads(res.read())

        self._paypal_s2s_validate(response)

        if response.get('state') == 'approved':
            paid = False
            if any(line.product_id.invoice_policy == 'delivery' for line in self.sale_order_id.order_line):
                for picking in self.sale_order_id.picking_ids:
                    picking.action_confirm()
                    picking.action_assign()
                    self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking.id)]}).process()
            self.sale_order_id.order_line._compute_invoice_status()
            self.sale_order_id._get_invoiced()
            context = {"active_model": 'sale.order', "active_ids": [self.sale_order_id.id], "active_id": self.sale_order_id.id}
            invoices = False
            if self.sale_order_id.invoice_status == 'to invoice':
                payment = self.env['sale.advance.payment.inv'].create({
                    'advance_payment_method': 'delivered',
                })
                invoices = self.sale_order_id._create_invoices(final=True)
                paid = True
            if self.sale_order_id.invoice_status != 'to invoice' and not paid:
                payment = self.env['sale.advance.payment.inv'].create({
                    'advance_payment_method': 'percentage',
                    'amount': 100
                })
                if not payment.product_id:
                    vals = payment._prepare_deposit_product()
                    payment.product_id = self.env['product.product'].create(vals)
                    self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', payment.product_id.id)

                sale_line_obj = self.env['sale.order.line']
                for order in self.sale_order_id:
                    if payment.advance_payment_method == 'percentage':
                        amount = order.amount_untaxed * payment.amount / 100
                    else:
                        amount = payment.fixed_amount
                    if payment.product_id.invoice_policy != 'order':
                        raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                    if payment.product_id.type != 'service':
                        raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                    taxes = payment.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                    if order.fiscal_position_id and taxes:
                        tax_ids = order.fiscal_position_id.map_tax(taxes, payment.product_id, order.partner_shipping_id).ids
                    else:
                        tax_ids = taxes.ids
                    context = {'lang': order.partner_id.lang}
                    analytic_tag_ids = []
                    for line in order.order_line:
                        analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
                    so_line = sale_line_obj.create({
                        'name': _('Down Payment: %s') % (time.strftime('%m %Y'),),
                        'price_unit': amount,
                        'product_uom_qty': 0.0,
                        'order_id': order.id,
                        'discount': 0.0,
                        'product_uom': payment.product_id.uom_id.id,
                        'product_id': payment.product_id.id,
                        'analytic_tag_ids': analytic_tag_ids,
                        'tax_id': [(6, 0, tax_ids)],
                        'is_downpayment': True,
                    })
                    del context
                    invoices = payment._create_invoice(order, so_line, amount)
            if invoices:
                invoices.with_context(context).action_post()
                for invoice in invoices:
                    self.create_payment(self.sale_order_id, invoice)
                    self._send_mail()
        return True

    def get_payment_vals(self, so, invoice):
        bank_journal = self.env['account.journal'].search([('type', '=', 'bank')], limit=1)
        payment_methods = bank_journal.inbound_payment_method_ids
        payment_method_id = payment_methods and payment_methods[0] or False
        return {
            'journal_id': bank_journal[0].id,
            'payment_method_id': payment_method_id.id,
            'communication': so.name,
            'invoice_ids': [(4, inv.id, None) for inv in invoice],
            'payment_type': 'inbound',
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': 'customer',
        }

    def create_payment(self, so, invoice):
        payment_vals = self.get_payment_vals(so, invoice)
        payment_vals.update({'payment_transaction_id': self.id})
        payment = self.env['account.payment'].create(payment_vals)
        payment.post()
        self.payment_id = payment.id
