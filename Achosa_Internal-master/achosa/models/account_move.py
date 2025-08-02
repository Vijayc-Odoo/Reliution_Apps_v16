# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.misc import get_lang
from odoo.exceptions import UserError

import logging, re

_logger = logging.getLogger("##### Achosa #####")

class AccountMove(models.Model):
    _inherit = "account.move"

    home_warranty = fields.Many2one("home.warranty", "Home Warranty")

    subscriptions = fields.Many2many("sale.subscription", compute="_get_subs", store=False)
    first_invoice = fields.Integer(string='First Invoice', compute="_compute_first_invoice")
    
    # SHARE URL FOR EMAIL
    share_url = fields.Char("SHARE URL",compute="_compute_get_terms",store=False)
    
    # Terms ID
    warranty_terms_id = fields.Many2one("product.attribute.value",string="Terms ID",
                                         compute="_compute_get_terms",store=False)
    
    # TERMS PDF URL FOR EMAIL
    warranty_terms_url = fields.Char("TERMS PDF URL",
                                         compute="_compute_get_terms",store=False)
    
    # TERMS PDF NAME FOR EMAIL
    warranty_terms_file_name = fields.Char("TERMS PDF NAME",
                                         compute="_compute_get_terms",store=False)
    
    # SERVICE MAP PDF URL FOR EMAIL
    service_map_url = fields.Char("SERVICE MAP PDF URL",
                                         compute="_compute_get_terms",store=False)
    
    # SERVICE MAP NAME FOR EMAIL
    service_map_file_name = fields.Char("SERVICE MAP NAME",
                                         compute="_compute_get_terms",store=False)
    
    
    @api.onchange('partner_id')
    def _get_invoice_address(self):
        for invoice_id in self:
            if invoice_id.partner_id.type == "invoice" and invoice_id.partner_id.parent_id:
                invoice_id.partner_id = invoice_id.partner_id.parent_id
    
    # compute terms attribute id, urls, and file names
    def _compute_get_terms(self):
        """
            This method is locating the first terms product attribute on invoice_line
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for invoice_id in self:
            invoice_id.share_url = base_url+invoice_id._get_share_url()
            invoice_id.warranty_terms_id = False
            invoice_id.warranty_terms_url = ""
            invoice_id.warranty_terms_file_name = ""
            invoice_id.service_map_url = base_url+"/web/content/"+str(self.env.company.service_map_attachment_id)
            invoice_id.service_map_file_name = self.env.company.service_map_attachment_name.replace(' ','_')+'.pdf'
            for invoice_line_id in invoice_id.invoice_line_ids:
                for template_attribute_value_id in invoice_line_id.product_id.product_template_attribute_value_ids:
                    if template_attribute_value_id.attribute_id.name == 'Terms':
                        invoice_id.warranty_terms_id = template_attribute_value_id.product_attribute_value_id
                        a = invoice_id.warranty_terms_id.attachment_ids
                        if a:
                            invoice_id.warranty_terms_url = base_url+a.website_url
                            invoice_id.warranty_terms_file_name = a.name.replace(' ','_')

    def _compute_first_invoice(self):
        """
            This method is check the created subscription invoice is first invoice or not
        """
        for invoice_id in self:
            invoice_id.first_invoice = True
            subscriptions = invoice_id.subscriptions
            renewal_product = invoice_id.check_renewal_product()
            if renewal_product:
                order_id = invoice_id.invoice_line_ids.mapped("sale_line_ids").order_id
                if order_id and len(order_id.invoice_ids) > 1:
                    invoice_id.first_invoice = False
                continue
            if not subscriptions:
                invoice_id.first_invoice = False
            subscription_id = subscriptions[0] if subscriptions else []
            if subscription_id and subscription_id.invoice_count > 1:
                invoice_id.first_invoice = False

    def get_paid_email_template(self):    
        
        inv_line_ids = self.invoice_line_ids.filtered(lambda line: line.product_id.paid_email_template_id)
        # mail_template_id = self.env.ref('achosa.hw_paid')

        # pull template ID from system parameters
        mail_template_id = int(self.env['ir.config_parameter'].search([('key', '=', 'sale.default_invoice_email_template')]).value)

        # use ID to browse for mail template record
        mail_template_id = self.env['mail.template'].browse(mail_template_id)
        mail_templates = inv_line_ids.mapped('product_id.paid_email_template_id')
        if len(mail_templates) > 0:
            mail_template_id = mail_templates[0]

        return mail_template_id

    def check_renewal_product(self):
        """
            This method is check the renewal product if the product is renewal it will return True otherwise
            return False and this will be used in email template
            @Ticket No: [AO-843]
            :return: renewal_product -> Boolean
        """
        renewal_product = False
        for invoice_line_id in self.invoice_line_ids:
            for template_attribute_value_id in invoice_line_id.product_id.product_template_attribute_value_ids:
                if template_attribute_value_id.attribute_id.name == 'Renewal Term':
                    renewal_product = True
                    break
        return renewal_product

    @api.depends('invoice_line_ids', 'payment_state')
    def _get_subs(self):
        for o in self:
            subs = []
            lines = o.invoice_line_ids.mapped("sale_line_ids")
            for l in lines:
                if l.subscription_id and (not l.subscription_id.id in subs):
                    subs.append(l.subscription_id.id)
            o.subscriptions = subs
            if o.payment_state == "paid":
                for sub in o.subscriptions:
                    sub._get_last_payment()
                    if sub.order_type == "Buyer": sub.date = sub._get_subscription_end_date()

            
            
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
                
        invoices = self.env['account.move'].search([['id','=',res.id]])
        for inv in invoices:
            if inv.partner_id.type == "invoice" and inv.partner_id.parent_id:
                inv.partner_id = inv.partner_id.parent_id
                
        return res
        
    def write(self, vals):
        """
        On new record update: set home_warranty
        :param vals:
        :return: bool - created
        """
        for item in self:
            _logger.log(logging.INFO, "self: " + str(self))
            if item.invoice_line_ids:
                if not item.home_warranty and "home_warranty" not in vals:
                    so = item.invoice_line_ids.mapped("sale_line_ids").mapped("order_id")
                    if so and so.home_warranty:
                        vals["home_warranty"] = so.home_warranty.id
        
        res = super(AccountMove, self).write(vals)
        
        if "state" in vals and self.ref == 'INV':
            invoices = self.env['account.move'].search([['name','=',self.ref]])
            for inv in invoices:
                inv.payment_state = 'paid'
                if inv.home_warranty and len(self.line_ids.payment_id.ids):
                    inv.home_warranty.with_context(nolog=True)._get_invoiced() 
        
        return res

    
    def _update_hw(self):
        if self.invoice_line_ids and not self.home_warranty:
            so = self.invoice_line_ids.mapped("sale_line_ids").mapped("order_id")
            if so and so.home_warranty:
                self.home_warranty = so.home_warranty.id

    def action_achosa_invoice_sent(self, template_id):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        lang = get_lang(self.env)
        if template_id and template_id.lang:
            # Below line caused errors when sending paid invoice email
            # lang = template_id._render_template(template_id.lang, 'account.move', self.id)
            lang = template_id.lang
        else:
            lang = lang.code
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_res_model='account.move',
            default_use_template=bool(template_id),
            default_is_print=False,
            default_template_id=template_id and template_id.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            model_description=self.with_context(lang=lang).type_name,
            force_email=True
        )
        return {
            'name': _('Send Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def _get_attachment_ids(self, line_ids):
        hw = self.home_warranty.product[0].default_code
        if not hw:
            value_ids = line_ids.mapped('product_id.attribute_line_ids').mapped('value_ids').ids
            return self.env['ir.attachment'].sudo().search(
                [('res_model', '=', 'product.attribute.value'), ('res_id', 'in', value_ids)]).ids
        
    def action_register_payment(self):
        """
            Inherit the method and update the context with custom variable for verify
            the payment is process from accounting module
            @Ticket: [AO-785] - Payment Email Revision
            :return: result -> Dict.
        """
        result = super(AccountMove, self).action_register_payment()
        result['context']['call_from_accounting_module'] = True
        return result

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    @api.depends('product_id')
    def _get_related_program(self):
        for rec in self:
            program = self.env['coupon.program'].search([('discount_line_product_id', '=', rec.product_id.id)])
            rec.related_program = program

    related_program = fields.One2many('coupon.program', 'discount_line_product_id',
                                      compute="_get_related_program", store=False)
