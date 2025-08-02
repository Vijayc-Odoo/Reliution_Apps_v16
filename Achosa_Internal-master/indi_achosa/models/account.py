# -*- coding: utf-8 -*-

import logging
from odoo import exceptions, api, fields, models, _
from odoo.exceptions import UserError

_LOGGER = logging.getLogger("##### Indimedi Achosa #####")

 
class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    def action_archive(self):
        attachment_ids = []
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'product.attribute.value'),
            ('res_id', '=', self.id)])
        for attach in attachments:
            attachment_ids.append(attach.id)
        if len(attachment_ids) > 0:
            msg = self.env['mail.channel'].search([('name', '=', 'TERMS')], limit=1)
            if msg:
                msg.message_post(
                    body='Archived the following terms documents.',
                    subject='Archive',message_type='comment',
                    subtype='mail.mt_comment', attachment_ids=attachment_ids)
                msg.model = 'product.attribute.value'
                msg.res_id = self.id
                msg.record_name = self.display_name
                for attach in attachments:
                    attach.model='mail.message'
                    attach.res_id = msg.id
                    attach.record_name = self.display_name

class HomeWarranty(models.Model):
    _inherit = 'home.warranty'
    
    def message_track(self, tracked_fields, initial_values):
        """ Track updated values. Comparing the initial and current values of
        the fields given in tracked_fields, it generates a message containing
        the updated values. """
        tracking = dict()

        if not tracked_fields:
            return tracking

        for record in self:
            changes = set()  # contains onchange tracked fields that changed
            tracking_value_ids = []
            # prevent multiple emails on creation
            if not record._context.get('nolog'):
                initial = initial_values[record.id]
                tracked_fields = self.fields_get(self._get_tracked_fields())
                for col_name, col_info in tracked_fields.items():
                    if col_name not in initial:
                        continue
                    initial_value = initial[col_name]
                    new_value = record[col_name]
                    if new_value != initial_value and (new_value or initial_value):
                        if col_info['type'] != 'boolean':
                            if not initial_value:
                                initial_value = ''
                            if not new_value:
                                new_value = ''
                        tracking_sequence = getattr(self._fields[col_name], 'tracking',
                                                getattr(self._fields[col_name], 'track_sequence', 100))  # backward compatibility with old parameter name
                        if tracking_sequence is True:
                            tracking_sequence = 100
#                         track_rec = self.env['mail.tracking.value'].create_tracking_values(initial_value, new_value, col_name, col_info, tracking_sequence)
#                         if tracking:
#                             tracking_value_ids.append([0, 0, track_rec])
                        changes.add(col_name)
                if len(changes) > 0:
                    template = self.env.ref('achosa.hw_updated')
                    template.with_context({'tracking': changes, 'author': self.env.user.display_name}).send_mail(
                        record.id)
            tracking[record.id] = changes, tracking_value_ids

        return tracking
    
    @api.model
    def create(self, vals):
        if vals.get('name') != "Web":
            seller_contact = False
            buyer_contact = False
            closing_contact = False
            realtor_contact = False
            if 'seller_contact' in vals and vals['seller_contact']:
                seller_contact = self.env['res.partner'].search([('id', '=', vals['seller_contact'])])
                #if seller_contact:
            seller_email = ''
            seller_phone = ''
            if 'seller_email' in vals and vals['seller_email']:
                seller_email = vals['seller_email']
            if 'seller_phone' in vals and vals['seller_phone']:
                seller_phone = vals['seller_phone']
                    
            if 'buyer_contact' in vals and vals['buyer_contact']:
                buyer_contact = self.env['res.partner'].search([('id', '=', vals['buyer_contact'])])
                #if buyer_contact:
            buyer_email = ''
            buyer_phone = ''
            if 'buyer_email' in vals and vals['buyer_email']:
                buyer_email = vals['buyer_email']
            if 'buyer_phone' in vals and vals['buyer_phone']:
                buyer_phone = vals['buyer_phone']
                    
            if 'closing_contact' in vals and vals['closing_contact']:
                closing_contact = self.env['res.partner'].search([('id', '=', vals['closing_contact'])])
                #if closing_contact:
            closing_email = ''
            closing_phone = ''
            if 'closing_email' in vals and vals['closing_email']:
                closing_email = vals['closing_email']
            if 'closing_phone' in vals and vals['closing_phone']:
                closing_phone = vals['closing_phone']
                    
            if 'realtor_contact' in vals and vals['realtor_contact']:
                realtor_contact = self.env['res.partner'].search([('id', '=', vals['realtor_contact'])])
                realtor_email = realtor_contact.email
                realtor_phone = realtor_contact.phone
                sale_person = realtor_contact.user_id
            else:
                realtor_email = ''
                realtor_phone = ''
                sale_person = False
            if 'realtor_salesperson' in vals and vals['realtor_salesperson']:
                sale_person = vals['realtor_salesperson']
            if 'realtor_email' in vals and vals['realtor_email']:
                realtor_email = vals['realtor_email']
            if 'realtor_phone' in vals and vals['realtor_phone']:
                realtor_phone = vals['realtor_phone']
            res = super(HomeWarranty, self).create(vals)
            if seller_contact and seller_email and seller_phone:
                seller_contact.write({'type': 'contact', 'email': seller_email, 'phone': seller_phone, 'supplier_rank': 1})
                self.env.cr.commit()
            if buyer_contact and buyer_email and buyer_phone:
                buyer_contact.write({'type': 'contact', 'email': buyer_email, 'phone': buyer_phone, 'customer_rank': 1})
                self.env.cr.commit()
            if closing_contact and closing_email and closing_phone:
                vendorType = closing_contact.vendor_type or 'Closing'
                closing_contact.write({'type': 'contact', 'vendor_type': vendorType,'email': closing_email, 'phone': closing_phone, 'supplier_rank': 1})
                self.env.cr.commit()
            if realtor_contact:
                vendorType = realtor_contact.vendor_type or 'Realtor'
                realtor_contact.write({'user_id': sale_person, 'type': 'contact', 'vendor_type': vendorType,'email': realtor_email, 'phone': realtor_phone, 'supplier_rank': 1})
                self.env.cr.commit()
        else:
            res = super(HomeWarranty, self).create(vals)
        return res
    
    
    def write(self, vals):
        seller_contact = False
        buyer_contact = False
        closing_contact = False
        realtor_contact = False
        if 'seller_contact' in vals and vals['seller_contact']:
            seller_contact = self.env['res.partner'].search([('id', '=', vals['seller_contact'])])
            #if seller_contact:
        seller_email = ''
        seller_phone = ''
        if 'seller_email' in vals and vals['seller_email']:
            seller_email = vals['seller_email']
        if 'seller_phone' in vals and vals['seller_phone']:
            seller_phone = vals['seller_phone']
                
        if 'buyer_contact' in vals and vals['buyer_contact']:
            buyer_contact = self.env['res.partner'].search([('id', '=', vals['buyer_contact'])])
            #if buyer_contact:
        buyer_email = ''
        buyer_phone = ''
        if 'buyer_email' in vals and vals['buyer_email']:
            buyer_email = vals['buyer_email']
        if 'buyer_phone' in vals and vals['buyer_phone']:
            buyer_phone = vals['buyer_phone']
                
        if 'closing_contact' in vals and vals['closing_contact']:
            closing_contact = self.env['res.partner'].search([('id', '=', vals['closing_contact'])])
            #if closing_contact:
        closing_email = ''
        closing_phone = ''
        if 'closing_email' in vals and vals['closing_email'] in [None, '', False]:
            if 'closing_contact' in vals and closing_contact.email not in [None, '', False]:
                vals['closing_email'] = closing_contact.email
                closing_email = vals['closing_email']
            if 'closing_contact' not in vals and self.closing_contact.email not in [None, '', False]:
                vals['closing_email'] = self.closing_contact.email
                closing_email = vals['closing_email']

        if 'closing_email' in vals and vals['closing_email'] not in [None, '', False]:
            closing_email = vals['closing_email']
        if 'closing_phone' in vals and vals['closing_phone']:
            closing_phone = vals['closing_phone']
                
        if 'realtor_contact' in vals and vals['realtor_contact']:
            realtor_contact = self.env['res.partner'].search([('id', '=', vals['realtor_contact'])])
            realtor_email = realtor_contact.email
            realtor_phone = realtor_contact.phone
            sale_person = realtor_contact.user_id
        else:
            realtor_email = ''
            realtor_phone = ''
            sale_person = False
        if 'realtor_salesperson' in vals and vals['realtor_salesperson']:
            sale_person = vals['realtor_salesperson']
        if 'realtor_email' in vals and vals['realtor_email']:
            realtor_email = vals['realtor_email']
        if 'realtor_phone' in vals and vals['realtor_phone']:
            realtor_phone = vals['realtor_phone']
        res = super(HomeWarranty, self).write(vals)
        if seller_contact and seller_email and seller_phone:
            seller_contact[0].write({'type': 'contact', 'email': seller_email, 'phone': seller_phone, 'supplier_rank': 1})
        elif self.seller_contact and seller_email and seller_phone:
            self.seller_contact.write({'type': 'contact', 'email': seller_email, 'phone': seller_phone, 'supplier_rank': 1})
        else:
            pass
        if buyer_contact and buyer_email and buyer_phone:
            buyer_contact[0].write({'type': 'contact', 'email': buyer_email, 'phone': buyer_phone, 'customer_rank': 1})
        elif self.buyer_contact and buyer_email and buyer_phone:
            self.buyer_contact.write({'type': 'contact', 'email': buyer_email, 'phone': buyer_phone, 'customer_rank': 1})
        else:
            pass
        if closing_contact and closing_email and closing_phone:
            vendorType = closing_contact.vendor_type or 'Closing'
            closing_contact[0].write({'type': 'contact', 'vendor_type': vendorType,'email': closing_email, 'phone': closing_phone, 'supplier_rank': 1})
        elif self.closing_contact and closing_email and closing_phone:
            vendorType = self.closing_contact.vendor_type or 'Closing'
            self.closing_contact.write({'type': 'contact', 'vendor_type': vendorType,'email': closing_email, 'phone': closing_phone, 'supplier_rank': 1})
        else:
            pass
        if realtor_contact and sale_person:
            vendorType = realtor_contact.vendor_type or 'Realtor'
            realtor_contact[0].write({'user_id': sale_person, 'type': 'contact', 'vendor_type': vendorType,'email': realtor_email, 'phone': realtor_phone, 'supplier_rank': 1})
        elif self.realtor_contact and realtor_contact and sale_person:
            vendorType = realtor_contact.vendor_type or 'Realtor'
            self.realtor_contact.write({'user_id': sale_person, 'type': 'contact', 'vendor_type': vendorType,'email': realtor_email, 'phone': realtor_phone, 'supplier_rank': 1})
        else:
            pass
        return res
    
    def _display_address(self):
        if self.property_street and self.property_state:
            return str(self.property_street) + '\n' + \
                   str(self.property_city) + ', ' + str(self.property_state.name) + ' ' + str(self.property_zip)
        else:
            return ''
    

class claims(models.Model):
    _inherit = "claims"

    def action_open_claims(self):
        self.ensure_one()
        return {
            'name': _('Claims'),
            'domain': [('customer', '=', self.customer.id)],
            'res_model': 'claims',
            'type': 'ir.actions.act_window',
            'views': [(False, 'list'), (False, 'form')],
            'view_mode': 'list,form',
            'target':'current',
            
        }

class AccountAsset(models.Model):
    _inherit = "account.asset"

    invoice_id = fields.Many2one("account.move", "Invoice")
    partner_id = fields.Many2one("res.partner", "Customer")
    city = fields.Char(related="partner_id.city", string="City")
    state_id = fields.Many2one(related="partner_id.state_id", string="State")
    
    @api.onchange('invoice_id')
    def _get_partner(self):
        for o in self:
            if o.invoice_id:
                o.partner_id = o.invoice_id.partner_id and o.invoice_id.partner_id.id or False
            else:
                o.partner_id = False

    def _recompute_board(self, depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, already_depreciated_amount, amount_change_ids):
        res = super(AccountAsset, self)._recompute_board(depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, already_depreciated_amount, amount_change_ids)
        for vals in res:
            vals['actual_invoice_id'] = self.invoice_id.id
            vals['home_warranty'] = self.invoice_id.home_warranty.id
        return res


class AccountMove(models.Model):
    _inherit = "account.move"

    actual_invoice_id = fields.Many2one("account.move", 'Original Invoice')

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        if res and res.move_type in ('out_invoice', 'out_refund') and not res.actual_invoice_id:
            res.actual_invoice_id = res.id
        return res

    def _auto_create_asset(self):
        create_list = []
        invoice_list = []
        auto_validate = []
        for move in self:
            if not move.is_invoice():
                continue

            for move_line in move.line_ids.filtered(lambda line: not (move.move_type in ('out_invoice', 'out_refund') and line.account_id.user_type_id.internal_group == 'asset')):
                if (
                    move_line.account_id
                    and (move_line.account_id.can_create_asset)
                    and move_line.account_id.create_asset != "no"
                    and not move.reversed_entry_id
                    and not (move_line.currency_id or move.currency_id).is_zero(move_line.price_total)
                    and not move_line.asset_ids
                ):
                    if not move_line.name:
                        raise UserError(_('Journal Items of {account} should have a label in order to generate an asset').format(account=move_line.account_id.display_name))
                    vals = {
                        'name': move_line.name,
                        'company_id': move_line.company_id.id,
                        'currency_id': move_line.company_currency_id.id,
                        'account_analytic_id': move_line.analytic_account_id.id,
                        'analytic_tag_ids': [(6, False, move_line.analytic_tag_ids.ids)],
                        'original_move_line_ids': [(6, False, move_line.ids)],
                        'state': 'draft',
                        'invoice_id': move.id,
                        'partner_id': move.partner_id and move.partner_id.id or False,
                    }
                    model_id = move_line.account_id.asset_model
                    if model_id:
                        vals.update({
                            'model_id': model_id.id,
                        })
                    auto_validate.append(move_line.account_id.create_asset == 'validate')
                    invoice_list.append(move)
                    create_list.append(vals)

        assets = self.env['account.asset'].create(create_list)
        for asset, vals, invoice, validate in zip(assets, create_list, invoice_list, auto_validate):
            if 'model_id' in vals:
                asset._onchange_model_id()
                asset._compute_first_depreciation_date()
                if validate:
                    asset.validate()
            if invoice:
                asset_name = {
                    'purchase': _('Asset'),
                    'sale': _('Deferred revenue'),
                    'expense': _('Deferred expense'),
                }[asset.asset_type]
                msg = _('%s created from invoice') % (asset_name)
                msg += ': <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>' % (invoice.id, invoice.name)
                asset.message_post(body=msg)
        return assets
    
    
class SaleOrder(models.Model):

    _inherit = "sale.order"
    
    customer_state = fields.Many2one(related='partner_id.state_id', string='State')
    
    
    
class Partner(models.Model):

    _inherit = "res.partner"
    
    def _get_state_code(self):
        return self.env['res.country.state'].search([('id','=',self.state_id.id)]).name
