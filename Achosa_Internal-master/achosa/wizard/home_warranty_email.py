# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HWEmail(models.TransientModel):
    _name = 'home.warranty.email'
    _rec_name = 'email_to'
    _description = "Home Warranty Send Email Selection"

    email_to = fields.Selection([
        ('seller__Realtor', 'Seller Invoice to Realtor'),
        ('seller__Seller', 'Seller Terms to Seller'),
        ('seller__Invoice', 'Seller Invoice...'),
        ('buyer_all_realtor', 'Buyer Invoice to Realtor'),
        ('buyer_all_buyer', 'Buyer Terms to buyer'),
        ('buyer_all_closing', 'Buyer Invoice to closing agent'),
        ('buyer_all_buyer_invoice','Invoice and Terms to Buyer'),
        ('buyer_all_invoice', 'Buyer Invoice...')],
        string="Send to", required=True)

    copy_coordinator = fields.Boolean("Copy Coordinator")


    def send_email(self):
        """
        Send email by template.
        """
        home_warranty = self.env['home.warranty'].with_context({'coordinator': self.copy_coordinator})\
            .browse(self.env.context.get('active_id'))
        if self.email_to in ('',''):
            raise UserError('Need to set recipient, use "Edit and Send Email"')
        if self.email_to.startswith('seller'):
            if not home_warranty.state in ('Seller','Buyer'):
                raise UserError('Must be in Seller or Buyer Status first')
            if not home_warranty.covered_seller_product_id:
                raise UserError('Need Seller Product')
            if self.email_to == 'seller__Realtor':
                if home_warranty.realtor_email:
                    p = 'achosa.seller_basic_Realtor'
                    if home_warranty.covered_seller_product_id.seller_realtor_email_template:
                        p = home_warranty.covered_seller_product_id.seller_realtor_email_template.id
                    home_warranty.send_invoice("seller", True, template_id=p)
                else:
                    raise UserError('Need Realtor email')
            elif self.email_to == 'seller__Invoice':
                if home_warranty.realtor_email:
                    p = 'achosa.seller_Invoice'
                    home_warranty.send_invoice(p, True)
                else:
                    raise UserError('Need Realtor email')
            elif self.email_to == 'seller__Seller':
                if home_warranty.seller_email:
                    p = 'achosa.seller_basic_Seller'
                    if home_warranty.covered_seller_product_id.seller_seller_email_template:
                        p = home_warranty.covered_seller_product_id.seller_seller_email_template.id
                    home_warranty.send_invoice("seller", True, template_id=p)
                else:
                    raise UserError('Need Seller email')
        elif self.email_to.startswith('buyer'):
            if not home_warranty.state == 'Buyer':
                raise UserError('Must be in Buyer Status first')
            if self.email_to == 'buyer_all_realtor' and not home_warranty.realtor_email:
                raise UserError('Need Realtor email')
            elif self.email_to == 'buyer_all_buyer' and not home_warranty.buyer_email:
                raise UserError('Need Buyer email')
            elif self.email_to == 'buyer_all_buyer_invoice' and not home_warranty.buyer_email:
                raise UserError('Need Buyer email')
            elif self.email_to == 'buyer_all_closing' and not home_warranty.closing_email:
                raise UserError('Need Closing Agent email')
            home_warranty.send_invoice('achosa.' + self.email_to, True)

    def edit_email(self):
        """
        Open email template.
        """
        home_warranty = self.env['home.warranty'].browse(self.env.context.get('active_id'))
        attachment_ids = []
        template_name = False
        template_id = False
        if self.email_to.startswith('seller'):
            if not home_warranty.state in ('Seller','Buyer'):
                raise UserError('Must be in Seller or Buyer Status first')
            if not home_warranty.covered_seller_product_id:
                raise UserError('Need Seller Product')
            if self.email_to == 'seller__Realtor':
                if home_warranty.realtor_email:
                    template_name = 'seller_basic_Realtor'
                    if home_warranty.covered_seller_product_id.seller_realtor_email_template:
                        template_id = home_warranty.covered_seller_product_id.seller_realtor_email_template.id
                else:
                    raise UserError('Need Realtor email')
            elif self.email_to == 'seller__Invoice':
                if home_warranty.realtor_email:
                    template_name = 'seller_Invoice'
                else:
                    raise UserError('Need Realtor email')
            elif self.email_to == 'seller__Seller':
                if home_warranty.seller_email:
                    template_name = 'seller_basic_Seller'
                    if home_warranty.covered_seller_product_id.seller_seller_email_template:
                        template_id = home_warranty.covered_seller_product_id.seller_seller_email_template.id
                else:
                    raise UserError('Need Seller email')
        else:
            if not home_warranty.state == 'Buyer':
                raise UserError('Must be in Buyer Status first')
            template_name = self.email_to
            for product in home_warranty.product_buyer:
                for attr in product.attribute_line_ids.mapped('value_ids'):
                    attachments = self.env['ir.attachment'].search([
                        ('res_model', '=', 'product.attribute.value'),
                        ('res_id', '=', attr.id)])
                    for attach in attachments:
                        attachment_ids.append(attach.id)
        if not template_id:
            try:
                template_id = self.env.ref('achosa.'+template_name).id
            except ValueError:
                template_id = False
        ctx = {
            'default_model': 'home.warranty',
            'default_res_id': home_warranty.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_auto_delete': False,
            'default_attachment_ids': [(4, id) for id in attachment_ids],
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
