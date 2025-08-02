from odoo import models, fields, api, _
from datetime import datetime

import logging, re

_logger = logging.getLogger("##### Achosa #####")


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_salesperson_domain(self):
        team_id = self.env.ref('sales_team.team_sales_department', raise_if_not_found=False)
        # return [('groups_id', 'in', self.env.ref('base.group_user').id),
        #         ('sale_team_id', '=', team_id.id if team_id else False)]
        return [('sale_team_id', '=', team_id.id if team_id else False)]

    claims = fields.One2many("claims", "customer", string="Claims")
    
    temporary = fields.Boolean("Temporary", default=False)

    # Survey Date
    last_survey_date = fields.Datetime("Last Survey Date")

    vendor_type = fields.Selection([("Realtor", "Realtor"), ("Tech", "Technician"), ("Closing", "Closing Agent"),
                                    ("Coordinator", "Coordinator")], "Vendor Type")
    home_warranty = fields.Many2one("home.warranty", string="Home Warranty")
    property_type = fields.Selection(related="home_warranty.property_type", string="Property Type")
    realtor_contact = fields.Many2one("res.partner", string="Realtor", related="home_warranty.realtor_contact",
                                      store=True)
    closing_contact = fields.Many2one("res.partner", string="Closing Agent", related="home_warranty.closing_contact",
                                      store=True)
    referrals = fields.One2many("res.partner", "realtor_contact", "Referrals")
    coordinator = fields.Many2one("res.partner", string="Coordinator")

    # Rating for Vendor
    vendor_rating = fields.Selection([("preferred", "Preferred"), ("notPreferred", "Not Preferred")], "Vendor Rating")

    # Services Zip Codes of Vendors
    zip_code_vendors = fields.One2many("vendor.zip.codes", "vendor", string="Services Zip Codes")
    user_id = fields.Many2one('res.users', string='Salesperson',
                              help='The internal user in charge of this contact.',
                              domain=lambda self: self._get_salesperson_domain())

    def _get_count_hw(self):
        for rec in self:
            rec.total_orders = 0
            if rec.vendor_type == "Realtor":
                hw = self.env['home.warranty'].search_read([('realtor_contact', '=', rec.id)], ['create_date'])
                rec.total_orders = len(hw)
                if (len(hw) > 0):
                    last_date = max([x['create_date'] for x in hw])
                    rec.days_since_order = (datetime.now() - last_date).days
                else:
                    rec.days_since_order = False

    def _get_count_claims(self):
        for rec in self:
            claims = self.env['claims'].search([('customer', '=', rec.id)])
            #_logger.log(logging.ERROR, claims)
            rec.total_claims = len(claims)

    total_orders = fields.Integer("Total Home Warranties Entered", compute="_get_count_hw", compute_sudo=True)
    total_claims = fields.Integer("Total Claims", compute="_get_count_claims")
    days_since_order = fields.Integer("Days Since Last Home Warranty Entered", compute="_get_count_hw",
                                      store=True, index=True)

    def action_view_home_warranties(self):
        """
        Open Seller Order
        :return:
        """
        self.ensure_one()
        return {
            'name': _('Home Warranties'),
            'domain': [('realtor_contact', '=', self.id)],
            'res_model': 'home.warranty',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {},
            'help': """
                        <p class="oe_view_nocontent_create">No Home Warranties for this Realtor.</p>
                        """,
        }

    def action_view_claims(self):
        """
        Open Claims
        :return:
        """
        self.ensure_one()
        return {
            'name': _('Claims'),
            'domain': [('customer', '=', self.id)],
            'res_model': 'claims',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {},
            'help': """
                        <p class="oe_view_nocontent_create">No claims for this customer.</p>
                        """,
        }

    def _display_address(self, without_company=False):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        args = {
            'state_code': self._get_state_code() or '',
            'state_name': self._get_state_name() or '',
            'country_code': self.country_id.code or '',
            'country_name': self._get_country_name(),
            'company_name': self.commercial_company_name or '',
        }
        for field in self._formatting_address_fields():
            args[field] = getattr(self, field) or ''
        if without_company:
            args['company_name'] = ''
        elif self.commercial_company_name:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args

    def _get_state_name(self):
        return self.env['res.country.state'].search([('id', '=', self.state_id.id)]).name

    def _get_state_code(self):
        return self.env['res.country.state'].search([('id', '=', self.state_id.id)]).code

    @api.onchange('phone', 'email', 'mobile', 'name', 'vendor_type')
    def link_crm(self):
        if self._origin.id != False:
            crm = self.env['crm.lead'].search([('partner_id', '=', self._origin.id)])
            for c in crm:
                c.contact_link_phone = self.phone
                c.contact_link_email = self.email
                c.contact_link_mobile = self.mobile
                c.contact_link_name = self.name
                c.contact_link_vendor_type = self.vendor_type


class Followers(models.Model):
    _inherit = 'mail.followers'

    @api.model
    def create(self, vals):
        if 'res_model' in vals and 'res_id' in vals and 'partner_id' in vals:
            dups = self.env['mail.followers'].search([('res_model', '=', vals.get('res_model')),
                                                      ('res_id', '=', vals.get('res_id')),
                                                      ('partner_id', '=', vals.get('partner_id'))])
            if len(dups):
                for p in dups:
                    p.sudo().unlink()
        return super(Followers, self).create(vals)