# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
import logging
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from .. import zillow
import requests

_logger = logging.getLogger("##### Achosa #####")


class HWReceiveCheck(models.TransientModel):
    _name = 'home.warranty.receive.check'
    _description = "Home Warranty Receive Check entry"

    home_warranty = fields.Many2one("home.warranty", "Home Warranty")

    value = fields.Integer("Value", compute="get_Zestiment")
    s_year_built = fields.Char("Year Built")
    standardized_land_use_type = fields.Char("Building Type")
    total_area_sq_ft = fields.Integer("Total livable SQFT")
    value_low = fields.Integer("Value Low - Estated Test")
    value_high = fields.Integer("Value High - Estated Test")
    estated_json = fields.Char("Estated Json")
    warning_text = fields.Char("Warning")

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True)

    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 required=True, readonly=True,
                                 default=1)

    # Realtor Sales Person
    realtor_salesperson = fields.Many2one("res.users", string="Sales Order Salesperson",
                                          ondelete="restrict", related="home_warranty.realtor_contact.user_id",
                                          store="True")

    buyer_email = fields.Char("Buyer Email", related="home_warranty.buyer_email",
                              store="True")

    # Seller's Coverage Start Date
    subscription_start_date = fields.Date("Subscription Start Date", default=datetime.today(),
                                          help="Subscription Start Date")

    @api.onchange('home_warranty')
    def _default_start(self):
        self.ensure_one()
        start_date = self.subscription_start_date
        home_warranty = self.env['home.warranty'].browse(self.env.context.get('active_id'))
        self.home_warranty = home_warranty
        _logger.info(home_warranty)
        if home_warranty:
            if home_warranty.estimated_closing_date:
                start_date = home_warranty.estimated_closing_date
            if (home_warranty.covered_buyer_term == 'NC') or (isinstance(home_warranty.covered_buyer_term, str)
                                                              and home_warranty.covered_buyer_term.isdigit()
                                                              and int(home_warranty.covered_buyer_term) == 48):
                start_date = fields.Date.from_string(start_date) + \
                             relativedelta(months=12)
        self.subscription_start_date = start_date

    def receive_check(self):
        """
        Apply the check received if valid, raise an UserError otherwise.
        """
        if self.home_warranty:
            home_warranty = self.home_warranty
        else:
            home_warranty = self.env['home.warranty'].browse(self.env.context.get('active_id'))
            self.home_warranty = home_warranty

        # Confirm and create invoice
        so = home_warranty.buyer_order
        if so:
            if self.realtor_salesperson:
                so.user_id = home_warranty.realtor_salesperson
            if not so.state == 'done':
                so.action_confirm()
            if not so.invoice_ids:
                so._create_invoices()
            inv = so.invoice_ids
            # inv.write({'invoice_sent': True}) #V13
            inv.write({'is_move_sent': True})  # V15
            if inv.state == 'draft':
                inv.post()
            if self.realtor_salesperson:
                inv.user_id = home_warranty.realtor_salesperson
            # Start Subscription
            sub = so.order_line.mapped('invoice_lines').mapped('subscription_id')
            if sub:
                sub.set_open()
                if self.realtor_salesperson:
                    sub.user_id = home_warranty.realtor_salesperson
                if self.subscription_start_date:
                    sub.date_start = self.subscription_start_date
                else:
                    sub.date_start = fields.Date.today()
                # set Subscription end date
                if (home_warranty.covered_buyer_term == 'NC') or (isinstance(home_warranty.covered_buyer_term, str)
                                                                  and home_warranty.covered_buyer_term.isdigit()
                                                                  and int(home_warranty.covered_buyer_term) == 48):
                    # New Construction is 48 from closing - first 12 not covered = 36 months from sub start
                    sub.date = fields.Date.from_string(sub.date_start) + relativedelta(months=36) \
                               - relativedelta(days=1)
                elif isinstance(home_warranty.covered_buyer_term,
                                str) and home_warranty.covered_buyer_term and home_warranty.covered_buyer_term.isdigit():
                    sub.date = fields.Date.from_string(sub.date_start) + \
                               relativedelta(months=int(home_warranty.covered_buyer_term)) - relativedelta(days=1)
                else:
                    sub.date = fields.Date.from_string(sub.date_start) + relativedelta(months=12) \
                               - relativedelta(days=1)
                sub.recurring_next_date = sub.date

            # Save Zillow info
            try:
                if self.value == 0:
                    self.get_Zestiment()
                home_warranty.estated_date = datetime.today()
                home_warranty.value = self.value
                home_warranty.s_year_built = self.s_year_built
                home_warranty.total_area_sq_ft = self.total_area_sq_ft
                home_warranty.standardized_land_use_type = self.standardized_land_use_type
                home_warranty.value_low = self.value_low
                home_warranty.value_high = self.value_high
                home_warranty.estated_json = self.estated_json
                home_warranty.estated_warning = self.warning_text
            except Exception as error:
                home_warranty.estated_warning = "Error loading Estated Data for " + home_warranty.name + "\n" + \
                                                "Try Zillow: \n" + \
                                                "https://www.zillow.com/homes/{}-{},-{},-{}_rb/".format(
                                                    home_warranty.property_street,
                                                    home_warranty.property_city,
                                                    home_warranty.property_state_code,
                                                    home_warranty.property_zip).replace(
                                                    ' ', '-')
                _logger.error("Error loading Estated Data for " + home_warranty.name + "\n" +
                              "Try Zillow: \n"
                              "https://www.zillow.com/homes/{}-{},-{},-{}_rb/".format(
                                  home_warranty.property_street,
                                  home_warranty.property_city,
                                  home_warranty.property_state_code,
                                  home_warranty.property_zip).replace(
                                  ' ', '-'))
                _logger.exception(error)

            # Open Receive Payment screen
            return {
                "type": "ir.actions.act_window",
                "res_model": "account.payment.register",
                'view_mode': 'form',
                'view_id': self.env.ref('achosa.view_account_payment_register_invoice_form_validate').id,
                "context": {'default_invoice_ids': [(4, inv.id)],
                            'default_payment_type': 'inbound',
                            'default_partner_type': 'customer',
                            'active_model': 'account.move',
                            'call_from_accounting_module': True,
                            'call_from_home_warranty': True,
                            'active_ids': inv.ids,
                            'active_id': inv.id},
                "target": "new",
                "name": _("Receive Payment"),
            }

    @api.depends('home_warranty')
    def get_Zestiment(self):
        url = ''
        self.s_year_built = False
        self.total_area_sq_ft = False
        self.standardized_land_use_type = False
        self.value = False
        self.value_low = False
        self.value_high = False
        company_id = self.company_id or self.env.company
        _logger.info(f"Method: get_Zestiment, Company: [{company_id.name}]")
        try:
            token = company_id.estated_token or 'h7FbxJPHSiFHJ4yRqcVO34raGj5Fd8'
            url = company_id.estated_url or 'https://sandbox.estated.com/v4/property?token={}&combined_address={},+{},+{}+{}'
            url = url.format(token, self.home_warranty.property_street, self.home_warranty.property_city,
                             self.home_warranty.property_state_code, self.home_warranty.property_zip).replace(' ', '+')
            _logger.info(url)
            response = requests.get(url)
            self.estated_json = response.json()
            if ('warnings' in response.json() and response.json()['warnings']):
                w = response.json()['warnings'][0]
                self.warning_text = str('{}: {} - {}'.format(w['code'], w['title'], w['description']))
                _logger.warning(response.json()['warnings'])
            if ('data' in response.json() and response.json()['data']):
                data = response.json()['data']
                _logger.info(data)
                self.s_year_built = str(data['structure']['year_built'])
                self.total_area_sq_ft = str(data['structure']['total_area_sq_ft'])
                self.standardized_land_use_type = str(data['parcel']['standardized_land_use_type'])
                self.value = str(data['valuation']['value'])
                self.value_low = str(data['valuation']['low'])
                self.value_high = str(data['valuation']['high'])
        except Exception as error:
            _logger.error("Error loading Estated Data for " + self.home_warranty.name + "\n" +
                          url)
            _logger.exception(error)
