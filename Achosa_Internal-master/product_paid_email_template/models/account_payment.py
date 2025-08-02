# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import models, SUPERUSER_ID, api

_LOGGER = logging.getLogger("##### Product Paid Email Template #####")


class AccountPayment(models.Model):
    _inherit = 'account.move'

    #Condition added in _send_mail_when_invoice_is_paid, so this function should be no longer needed 03/01/2023
    
    # def _check_mail_already_sent(self, model_name, invoice_id, template_id):
    #     """
    #         Check the mail is already sent, if Yes then skip to send again.
    #     """
    #     subject = template_id.subject
    #     rec_subject = template_id._render_template(subject, 'account.move', [self.id])
    #     if self.env['mail.message'].search(
    #             [['model', '=', model_name], ['res_id', '=', invoice_id.id], ['subject', '=', rec_subject.get(self.id)]],
    #             limit=1):
    #         return True
    #     return False



    def _send_mail_when_invoice_is_paid(self, mail_template_id=False):
        # if self._context.get('call_from_accounting_module', False):
        #     return True
        message_post_templates = []
        if self.env.su:
            # sending mail in sudo was meant for it being sent from superuser
            self = self.with_user(SUPERUSER_ID)
        for invoice_id in self.filtered(lambda x: x.move_type == 'out_invoice' and x.payment_state == 'paid'):
            _LOGGER.info(f"Method: [_send_mail_when_invoice_is_paid], Invoice: [{invoice_id.id}]")
            # send template only on customer invoice
            # subscribe the partner to the invoice
            # if invoice_id.partner_id not in invoice_id.message_partner_ids:
            #     invoice_id.message_subscribe([invoice_id.partner_id.id])
            for line in invoice_id.invoice_line_ids.filtered(lambda line: line.product_id.paid_email_template_id):
            # the continue condition below with message_post_templates should be more effiecient than the commented code below
            
                # if self._check_mail_already_sent(model_name='account.move', invoice_id=invoice_id,
                #                                  template_id=line.product_id.paid_email_template_id):
                #     _LOGGER.info(
                #         f"Skip the invoice because of the mail is already sent of Invoice: [{invoice_id.name}], "
                #         f"Product: [{line.product_id.name}], "
                #         f"Product Email Template: [{line.product_id.paid_email_template_id}]")
                #     continue
                paid_email_template_id = mail_template_id if mail_template_id else line.product_id.paid_email_template_id
                _LOGGER.info(f"Product Email Template: [{line.product_id.paid_email_template_id}]")
                # condition to prevent sending same email template twice
                if mail_template_id in message_post_templates:
                    continue
                    
                # add template id to be used in continue condition
                message_post_templates.append(paid_email_template_id.id)
                invoice_id.message_post_with_template(
                    paid_email_template_id.id,
                    composition_mode="comment",
                    email_layout_xmlid="mail.mail_notification_light"
                )
        return True


