from odoo import models, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def action_validate_invoice_payment(self):
        """
            Usage: This method is validate the invoice
            :return: Boolean
        """
        self.action_create_payments()
        move_id = self.line_ids.move_id
        if move_id:
            for order_id in move_id[0].invoice_line_ids.sale_line_ids.order_id:
                order_id.home_warranty._get_invoiced()
        return True

    def action_validate_and_choose_email(self):
        self.with_context(mail_template_id=self.env.ref('achosa.hw_paid')).action_create_payments()
        move_id = self.line_ids.move_id
        if move_id:
            mail_template_id = move_id.get_paid_email_template()
            template_id = mail_template_id if mail_template_id else self.env.ref('achosa.hw_paid', raise_if_not_found=False)
            result = move_id.action_achosa_invoice_sent(template_id)
            result['context']['active_ids'] = move_id.ids
            result['context']['active_model'] = 'account.move'
            return result
        return True

    def action_validate_invoice_payment_email(self):
        context = self._context.copy()
        move_id = self.line_ids.move_id
        if len(move_id) > 1:
            # For multiple invoices, there is account.register.payments wizard
            raise UserError(_("This method should only be called to process a single invoice's payment."))
        self.with_context(mail_template_id=self.env.ref('achosa.hw_paid')).action_create_payments()
        if move_id:
            self.with_context(context=context).send_email()
        return True

    def _check_automation_action(self):
        __action_done = list(self._context.get('__action_done', {}).keys())
        if __action_done and str(__action_done[0]).__contains__('base.automation'):
            return True
        return False

    def _check_mail_exists(self, model_name, resource_id, template_id):
        """
            Check the mail is already sent, if Yes then skip to send again.
            @Ticket: AO-782
        """
        if self.env['mail.message'].search(
                [['model', '=', model_name], ['res_id', '=', resource_id.id], ['subject', '=', template_id.subject]],
                limit=1):
            return True
        return False

    def send_email(self):
        call_from_accounting_module = self._context.get('call_from_accounting_module', False)
        if self._check_automation_action() and call_from_accounting_module:
            return True
        try:
            template = self.env.ref('achosa.hw_paid')
        except ValueError:
            return
        if not self.line_ids.move_id:
            return True
        invoice_id = self.line_ids.move_id[0]
        # Check the mail is already sent, if Yes then skip to send again [Ticket: AO-782]
        if (not call_from_accounting_module) and self._check_mail_exists('account.move', invoice_id, template):
            return True
        attachment_ids = template.attachment_ids.ids.copy()
        for line in invoice_id.invoice_line_ids:
            for attr in line.product_id.attribute_line_ids.mapped('value_ids'):
                attachments = self.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'product.attribute.value'),
                    ('res_id', '=', attr.id)])
                for attach in attachments:
                    attachment_ids.append(attach.id)
            if line.sale_line_ids.order_id:
                hw = line.sale_line_ids.order_id.home_warranty
                hw._get_invoiced()

        mail_values = {
            'attachment_ids': [(4, id) for id in attachment_ids]
        }

        msg_id = template.send_mail(invoice_id.id, email_values=mail_values)
        return msg_id