# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging, re

_logger = logging.getLogger("##### Achosa #####")


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _prepare_payment_moves(self):
        res = super(AccountPayment, self)._prepare_payment_moves()
        for vals in res:
            vals['home_warranty'] = self.invoice_ids[0].home_warranty.id
            vals['actual_invoice_id'] = self.invoice_ids[0].id
        return res

    # def post(self):
    #     """ Overridden to sending the Payment Receipt mail to customer.
    #     @Ticket: [AO-782] - Payment Receipt - Send by Email
    #     :return: result
    #     """
    #     result = super(AccountPayment, self).post()
    #     for record in self:
    #         record.send_payment_receipt_by_mail()
    #     return result

    def send_payment_receipt_by_mail(self):
        """
            Usage: This method is sent the Payment Receipt mail to the customer once the Payment has done.
            @Ticket: [AO-782] - Payment Receipt - Send by Email
            :return: Boolean
        """
        self.ensure_one()
        paid_email_template_id = self.env.ref('account.mail_template_data_payment_receipt', False)
        if self._context.get("call_from_accounting_module", False):
            _logger.info(f"Skip to send the mail because the the method called from #Validate and Email# button, "
                         f"Ticket: [AO-785], Email Template: [{paid_email_template_id.name if paid_email_template_id else ''}]")
            return True
        invoice_id = self.invoice_ids[0] if self.invoice_ids else []
        _logger.info(f"Payment Receipt By Mail Process Started...!, Payment ID: {self.ids}")
        if paid_email_template_id and invoice_id:
            if self.state == 'posted' and self.reconciled_invoice_ids:
                if self._check_mail_exists('account.move', invoice_id, paid_email_template_id):
                    _logger.info(f"Skip to send the mail due to mail already sent! Payment ID: {self.ids}, "
                                 f"Invoice Ids: {invoice_id.ids}")
                    return True
                try:
                    mail_id = paid_email_template_id.send_mail(self.id, email_values={'model': 'account.move',
                                                                                      'res_id': invoice_id.id})
                    message = f"Account Payment ID: {self.ids}, Invoice Ids: {invoice_id.ids}, " \
                              f"Email ID: {mail_id}"
                except Exception as exception:
                    message = f"Exception occur while sending the mail, Exception: {exception}, " \
                              f"Account Payment ID: {self.ids}, Invoice Ids: {invoice_id.ids}"

                self.env['ir.logging'].create_ir_logging_record(
                    function_name="[AO-782] - Payment Receipt - Send by Email",
                    message=message, path='achosa/models/account_payment.py')
        _logger.info(f"Payment Receipt By Mail Process Ended...!, Payment ID: {self.ids}")
        return True
