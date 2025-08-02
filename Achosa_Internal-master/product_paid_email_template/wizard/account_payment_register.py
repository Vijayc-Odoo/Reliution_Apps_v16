import logging
from odoo import models, _

_logger = logging.getLogger("##### Achosa #####")

class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"
    
    def action_create_payments(self):
        result = super(AccountPaymentRegister, self).action_create_payments()
        move_id = self.line_ids.move_id
        mail_template_id = self._context.get('mail_template_id', self.env['mail.template']) or self.env['mail.template']
        mail_template_id = mail_template_id if len(mail_template_id) > 0 else move_id.get_paid_email_template()
        if mail_template_id:
            self.line_ids.move_id._send_mail_when_invoice_is_paid(mail_template_id)
        return result
