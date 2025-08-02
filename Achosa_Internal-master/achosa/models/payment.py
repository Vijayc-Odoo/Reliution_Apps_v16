# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import os

from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger("##### Achosa #####")


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    # --------------------------------------------------
    # Sale management
    # --------------------------------------------------

    def _post_process_after_done(self, **kwargs):

        res = super(PaymentTransaction, self)._post_process_after_done()
        
        for p in self:
            orders = p.sale_order_ids

            for order in orders:
                if order.home_warranty:
                    home_warranty = order.home_warranty
                    # update invoice status
                    order.home_warranty._get_invoiced()

                    if order.order_type == 'Buyer' and 'Auth' in p.acquirer_id.name:
                        # Get Payment
                        payment = self.env["account.payment"].search([("payment_transaction_id","=",self.id)])
                        # Get invoices
                        if payment:
                            # payment[0].send_email()
                            if payment.invoice_ids[0]:
                                _logger.log(logging.INFO, "Payment on invoice: "+payment.invoice_ids[0].name)
                            else:
                                _logger.log(logging.INFO, "Payment: "+payment.name)
                        else:
                            _logger.log(logging.WARN, "Payment NOT FOUND")
                        # set subscription dates
                        start_date = datetime.today()
                        if home_warranty.estimated_closing_date:
                            start_date = home_warranty.estimated_closing_date
                        if (home_warranty.covered_buyer_term == 'NC') or \
                                (isinstance(home_warranty.covered_buyer_term, str)
                                 and home_warranty.covered_buyer_term.isdigit()
                                 and int(home_warranty.covered_buyer_term) == 48):
                            start_date = fields.Date.from_string(start_date) + \
                                         relativedelta(months=12)
                        # Start Subscription
                        sub = order.order_line.mapped('invoice_lines').mapped('subscription_id')
                        if sub:
                            sub.set_open()
                            sub.user_id = home_warranty.realtor_salesperson
                            sub.date_start = start_date
                            # set Subscription end date
                            if (home_warranty.covered_buyer_term == 'NC') or \
                                    (isinstance(home_warranty.covered_buyer_term, str)
                                     and home_warranty.covered_buyer_term.isdigit()
                                     and int(home_warranty.covered_buyer_term) == 48):
                                # New Construction is 48 from closing - first 12 not covered = 36 months from sub start
                                sub.date = fields.Date.from_string(sub.date_start) + relativedelta(months=36) \
                                           - relativedelta(days=1)

                            elif isinstance(home_warranty.covered_buyer_term, str) and home_warranty.covered_buyer_term and home_warranty.covered_buyer_term.isdigit():
                                sub.date = fields.Date.from_string(sub.date_start) + \
                                           relativedelta(months=int(home_warranty.covered_buyer_term)) - relativedelta(
                                    days=1)
                            else:
                                sub.date = fields.Date.from_string(sub.date_start) + relativedelta(months=12) \
                                           - relativedelta(days=1)
                            sub.recurring_next_date = sub.date
                            _logger.log(logging.INFO, "Order Paid: %s with %s - Subscription started" %
                                        (order.name, p.acquirer_id.name))
                            return res

                if self.acquirer_id:
                    _logger.log(logging.INFO, "Order Paid: %s with %s" % (order.name, p.acquirer_id.name))
                else:
                    _logger.log(logging.INFO, "Order Paid: %s" % order.name)

        return res
    
    def _invoice_sale_orders(self):
        for trans in self.filtered(lambda t: t.sale_order_ids):
            ctx_company = {'company_id': trans.acquirer_id.company_id.id,
                           'with_company': trans.acquirer_id.company_id.id}
            trans = trans.with_context(**ctx_company)
            trans.sale_order_ids._force_lines_to_invoice_policy_order()
            invoices = trans.sale_order_ids._create_invoices()
            trans.invoice_ids = [(6, 0, invoices.ids)]
                     
            
class PaymentAcquirerAuthorize(models.Model):
    _inherit = 'payment.acquirer'           
            
    def _update_authorize_dev_tokens(self):
        company_id = self.env.company
        authorize = self.env['payment.acquirer'].search([("provider","=","authorize")])
        for auth in authorize:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            if ".dev.odoo.com" in base_url and auth.state == "test" and auth.authorize_login == "dummy" and os.environ.get('ODOO_STAGE') == "staging":
                authorize_login = company_id.authorize_login_test
                authorize_transaction_key = company_id.authorize_transaction_key_test
                authorize_signature_key = company_id.authorize_signature_key_test
                _logger.info(f"Company: [{company_id.name}], Authorize Login: [{authorize_login}], "
                             f"Authorize Transaction Key: [{authorize_transaction_key}], "
                             f"Authorize Signature Key: [{authorize_signature_key}]")
                auth.write({"authorize_login":authorize_login, "authorize_transaction_key":authorize_transaction_key, "authorize_signature_key":authorize_signature_key})
                _logger.log(logging.INFO, "Authorize transaction failed, updating test credentials for Authorize.  Please try the transaction again in a few minutes.")
