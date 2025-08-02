from odoo import exceptions, models, fields, api, tools, _
import logging
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from lxml import etree
import requests
from .. import zillow
import json

_logger = logging.getLogger("##### Achosa #####")


class HomeWarranty(models.Model):
    _name = 'home.warranty'
    _description = 'Home Warranty'
    _inherit = ['mail.thread']
    _inherits = {}
    _order = 'id'

    # region Zillow Fields

    company_id = fields.Many2one('res.company', string='Company ID', change_default=True,
                                 required=True, readonly=True,
                                 default=1)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True)

    Zestimate = fields.Selection(
        [('< $100k', '< $100k'), ('$100k-$199,999', '$100k-$199,999'), ('$200k-$299,999', '$200k-$299,999'),
         ('$300k-$399,999', '$300k-$399,999'),
         ('$400k-$499,999', '$400k-$499,999'), ('$500k-$599,999', '$500k-$599,999'),
         ('$600k-$999,999', '$600k-$999,999'), ('$1M+', '$1M+')], string="Zestimate®")

    finished_sqft = fields.Selection(
        [('< 1000', '< 1000'), ('1000-1499', '1000-1499'), ('1500-1999', '1500-1999'), ('2000-2499', '2000-2499'),
         ('2500-2999', '2500-2999'), ('3000-3499', '3000-3499'),
         ('3500-3999', '3500-3999'), ('4000-4499', '4000-4499'), ('4500-4999', '4500-4999'), ('5000-5499', '5000-5499'),
         ('5500-5999', '5500-5999'), ('6000+', '6000+')], string="Finished SQFT")

    year_built = fields.Selection(
        [('< 1900', '< 1900'), ('1900-1949', '1900-1949'), ('1950-1959', '1950-1959'), ('1960-1969', '1960-1969'),
         ('1970-1979', '1970-1979'),
         ('1980-1989', '1980-1989'), ('1990-1999', '1990-1999'), ('2000-2009', '2000-2009'), ('2010-2019', '2010-2019'),
         ('2020-2029', '2020-2029')], string="Year Built")

    link_text = fields.Char("Link to Zillow Text")
    links = fields.Char("Link to Zillow")
    type = fields.Char("Zillow Property Type")

    x_Zestimate = fields.Char("Zestimate® - Zillow test")
    x_finished_sqft = fields.Char("Finished SQFT - Zillow test")
    x_year_built = fields.Char("Year Built - Zillow test")

    # endregion

    # region Estated

    s_year_built = fields.Char("Year Built - Estated Test")
    value = fields.Integer("Value - Estated Test")
    value_low = fields.Integer("Value Low - Estated Test")
    value_high = fields.Integer("Value High - Estated Test")
    standardized_land_use_type = fields.Char("Building Type - Estated Test")
    total_area_sq_ft = fields.Integer("Total livable SQFT - Estated Test")
    estated_json = fields.Char("Estated Json")
    estated_warning = fields.Char("Estated Warning")
    estated_date = fields.Date("Estated Date")

    # endregion

    # Name
    name = fields.Char("Name",
                       tracking=True, copy=False)

    # Status
    state = fields.Selection([('draft', 'Draft'), ('Seller', 'Seller Ordered'), ('Buyer', 'Buyer Ordered'),
                              ('Owner', 'Owner')], string="Status",
                             tracking=True, default='draft')

    submitter = fields.Many2one("res.users", string="Submitter", ondelete="restrict",
                                tracking=True)

    # region Realtor Fields

    # Contact (Realtor)
    realtor_contact = fields.Many2one("res.partner", string="Contact (Realtor)", ondelete="restrict",
                                      tracking=True)

    # Realtor Company
    realtor_company = fields.Char(
        "Realtor Company", compute="_get_realtor_company", store=True)

    # Realtor Email
    realtor_email = fields.Char("Realtor Email", related="realtor_contact.email",
                                store="True", tracking=True)

    # Realtor Name
    realtor_name = fields.Char("Realtor Name", related="realtor_contact.name",
                               store="True", tracking=True)

    # Realtor Phone
    realtor_phone = fields.Char("Realtor Phone", related="realtor_contact.phone",
                                store="True", tracking=True)

    # Realtor Sales Person
    realtor_salesperson = fields.Many2one("res.users", string="Sales Person",
                                          ondelete="restrict", related="realtor_contact.user_id",
                                          store="True", tracking=True)

    # Realtor Representing Buyer
    realtor_representing_buyer = fields.Boolean("Realtor Representing Buyer",
                                                tracking=True)

    # Realtor Representing Seller
    realtor_representing_seller = fields.Boolean("Realtor Representing Seller",
                                                 tracking=True)

    realtor_coordinator = fields.Char(
        "Realtor Coordinator Email", compute="_get_coordinator")

    @api.depends('realtor_contact')
    def _get_coordinator(self):
        for rec in self:
            # emails = []
            # if rec.realtor_contact:
            #     for c in rec.realtor_contact.child_ids:
            #         if c.vendor_type == "Coordinator":
            #             emails.append(c.email)
            # rec.realtor_coordinator = ",".join(emails)
            if rec.realtor_contact and rec.realtor_contact.coordinator:
                rec.realtor_coordinator = rec.realtor_contact.coordinator.email
            else:
                rec.realtor_coordinator = ''

    @api.depends('realtor_name')
    def _get_realtor_company(self):
        for rec in self:
            if rec.realtor_contact.company_name:
                rec.realtor_company = rec.realtor_contact.company_name
            else:
                rec.realtor_company = rec.realtor_contact.parent_id.name

    # endregion

    # region Property Fields

    # Street
    property_street = fields.Char("Street",
                                  tracking=True)

    # Street2
    property_street2 = fields.Char("Street2",
                                   tracking=True)

    # City
    property_city = fields.Char("City",
                                tracking=True)

    # Zip
    property_zip = fields.Char("Zip",
                               tracking=True)

    # State
    property_state = fields.Many2one("res.country.state", string="State", ondelete="restrict",
                                     tracking=True, domain=[['enable_home_warranty', '=', True]])

    # State Code
    property_state_code = fields.Char("State Code",
                                      tracking=True, compute="_update_property_state")

    # Property Type
    property_type = fields.Selection(
        [['Single Family Home', 'Single Family Home'], ['Townhome/Condo', 'Townhome/Condo'], ['Duplex', 'Duplex'],
         ['Triplex', 'Triplex'], ['Fourplex', 'Fourplex']], string="Property Type",
        tracking=True)

    # endregion

    # region Seller Fields

    # Contact (Seller)
    seller_contact = fields.Many2one("res.partner", string="Contact (Seller)", ondelete="restrict",
                                     tracking=True)

    # Seller Email
    seller_email = fields.Char("Seller Email", related="seller_contact.email",
                               store="True", tracking=True)

    # Seller Name
    seller_name = fields.Char("Seller Name", related="seller_contact.name",
                              store="True", tracking=True)

    # Seller Phone
    seller_phone = fields.Char("Seller Phone", related="seller_contact.phone",
                               store="True", tracking=True)

    # Seller's Coverage
    covered_sellers_coverage = fields.Boolean("Seller's Coverage",
                                              tracking=True)

    # Seller's Product
    covered_seller_product = fields.Selection(
        [["Seller's Basic", 'Basic'], ["Seller's Essentials - NoMa", 'Essentials (No HVAC Maintenance)'],
         ["Seller's Essentials - Main", 'Essentials (Proof of HVAC Maintenance)']], string="Seller's Product Old",
        tracking=True)
    covered_seller_product_id = fields.Many2one("product.attribute.value", string="Seller's Product",
                                                ondelete="restrict",
                                                tracking=True)

    # Seller's Coverage Start Date
    coverage_start_date = fields.Date("Coverage Start Date",
                                      tracking=True, default=datetime.today(),
                                      help="Seller's Coverage Start Date")

    seller_mismatch = fields.Boolean("Contact Seller Mismatch", compute='_compute_orders',
                                     store=True, compute_sudo=True)

    # endregion

    # region Buyer Fields
    # Contact (Buyer)
    buyer_contact = fields.Many2one("res.partner", string="Contact (Buyer)", ondelete="restrict",
                                    tracking=True)

    # Buyer Email
    buyer_email = fields.Char("Buyer Email", related="buyer_contact.email",
                              store="True")

    # Buyer Name
    buyer_name = fields.Char("Buyer Name", related="buyer_contact.name",
                             store="True", tracking=True,)

    # Buyer Phone
    buyer_phone = fields.Char("Buyer Phone", related="buyer_contact.phone",
                              store="True", tracking=True)

    # Rental Property
    rental_property = fields.Selection(
        [('True', 'Yes'), ('False', 'No')], string='Rental Property')
    # rental_property = fields.Boolean("Rental Property", ondelete="restrict",
    # tracking=True)

    # Boolean to hide rental property checkbox if state is not listed in Non
    # Owner Occupied Field
    hide_rental_property = fields.Boolean("Hide Rental Property",
                                          tracking=True)

    # Paying As
    paying_as = fields.Selection(
        [('buyer', 'Buyer'), ('realtor', 'Realtor')], string='Paying As')

    # ID for Non-Owner Occupied Addon
    rental_addon_id = fields.Integer(
        "Rental Addon ID", compute='_compute_addon_id')
    # ID for Conserve Addon
    conserve_id = fields.Integer(
        "Conserve ID", compute='_compute_addon_id')
    # ID for Conserve Plus Addon
    conserve_plus_id = fields.Integer(
        "Conserve Plus ID", compute='_compute_addon_id')
    non_owner_addon_id = fields.Integer(
        "Non Owner Addon ID", compute='_compute_addon_id')

    covered_buyer_product = fields.Selection(
        [['Essentials', 'Essentials'], ['1st Choice', '1st Choice']], string="Buyer's Product ",
        tracking=True)
    covered_buyer_product_id = fields.Many2one("product.attribute.value", string="Buyer's Product",
                                               ondelete="restrict",
                                               tracking=True)

    # Owner's Product
    covered_owner_product_id = fields.Many2one("product.attribute.value", string="Homeowner's Product",
                                               ondelete="restrict",
                                               tracking=True)

    # Term
    # Update get_covered_term_id function if non-int selection is added
    covered_buyer_term = fields.Selection(
        [('12', '12 Months'), ('18', '18 Months'), ('24', '24 Months'), ('36', '36 Months'),
         ('48', 'New Construction - (Deprecated)'),
         ('NC', 'New Construction')], string="Term",
        tracking=True)
    
    @api.onchange('covered_buyer_term')
    def _onchange_subscription_term(self):
        for hw in self:
            hw_term = hw.covered_buyer_term
            #need to reference sub._origin to get origin onchange record
            subs = [sub._origin for sub in hw.subscription if sub.stage_id.id not in ['4', '5']]
            for sub in subs:
                sub['template_id'] = sub.get_sub_term_template(hw_term)
                if sub.recurring_next_date:
                    sub['recurring_next_date'] = sub.date_start + relativedelta(months=int(hw_term)) 

    # Buyer's Coverage
    covered_buyers_coverage = fields.Boolean("Buyer's Coverage",
                                             tracking=True)

    # Buyer's Coverage Estimated Closing Date
    estimated_closing_date = fields.Date("Estimated Closing Date",
                                         tracking=True,
                                         help="Buyer's Coverage Estimated Closing Date")

    buyer_mismatch = fields.Boolean("Contact Buyer Mismatch", compute='_compute_orders',
                                    store=True, compute_sudo=True)

    # region Buyer Item Fields
    # widget="many2many_checkboxes"/>
    covered_buyer_addons = fields.Many2many("product.attribute.value", "home_warranty_buyer_addons",
                                            "home_warranty_id", "terms_id",
                                            string="Buyer's Addons")

    # Additional Pool or Spa
    covered_additional_pool_spa = fields.Boolean("Additional Pool or Spa",
                                                 tracking=True)

    # Additional Refrigerator
    covered_additional_refrigerator = fields.Boolean("Additional Refrigerator",
                                                     tracking=True)

    # Jetted Bathtub
    covered_jetted_bathtub = fields.Boolean("Jetted Bathtub",
                                            tracking=True)

    # Pool & Spa (shared equip)
    covered_pool_spa_shared_equip = fields.Boolean("Pool & Spa (shared equip)",
                                                   tracking=True)

    # Septic System
    covered_septic_system = fields.Boolean("Septic System",
                                           tracking=True)

    # Stand Alone Freezer
    covered_stand_alone_freezer = fields.Boolean("Stand Alone Freezer",
                                                 tracking=True)

    # Stand Alone Ice Maker
    covered_stand_alone_ice_maker = fields.Boolean("Stand Alone Ice Maker",
                                                   tracking=True)

    # Water Softener
    covered_water_softener = fields.Boolean("Water Softener",
                                            tracking=True)

    # Well Water Pump
    covered_well_water_pump = fields.Boolean("Well Water Pump",
                                             tracking=True)

    # Mini-split System
    covered_mini_split = fields.Boolean("Mini-Split System",
                                        tracking=True)

    # endregion
    # endregion

    # region Owner Fields

    # Contact (Owner)
    owner_contact = fields.Many2one("res.partner", string="Contact (Owner)", ondelete="restrict",
                                    tracking=True)

    # Owner Email
    owner_email = fields.Char("Owner Email", related="seller_contact.email",
                              store="True", tracking=True)

    # Owner Name
    owner_name = fields.Char("Owner Name", related="seller_contact.name",
                             store="True", tracking=True)

    # Owner Phone
    owner_phone = fields.Char("Owner Phone", related="seller_contact.phone",
                              store="True", tracking=True)

    # Owner's Coverage
    covered_owners_coverage = fields.Boolean("Owner's Coverage",
                                             tracking=True)

    # endregion

    # region Closing Agent / Business Fields

    # Closing Business City
    closing_business_city = fields.Char("Closing Business City",
                                        tracking=True,
                                        help="Closing Business City")

    # Title, Escrow, Attorney, Closing Company Name
    closing_business_name = fields.Char("Closing Business Name",
                                        tracking=True,
                                        help="Title, Escrow, Attorney, Closing Company Name")

    # Closing Business Zip Code
    closing_business_zip = fields.Char("Closing Business Zip",
                                       tracking=True,
                                       help="Closing Business Zip Code")

    # Closing Business State
    closing_business_state = fields.Selection([('OH', 'Ohio')], string="Closing Business State",
                                              tracking=True,
                                              help="Closing Business State")

    # Closing Business Street Address
    closing_business_street = fields.Char("Closing Business Street",
                                          tracking=True,
                                          help="Closing Business Street Address")

    # Closing Business Street 2
    closing_business_street2 = fields.Char("Closing Business Street 2",
                                           tracking=True,
                                           help="Closing Business Street 2")

    # Closing Agent Partner
    closing_contact = fields.Many2one("res.partner", string="Contact (Closing Agent)", ondelete="restrict",
                                      tracking=True)

    # Closing Email
    closing_email = fields.Char("Closing Email", store="True", tracking=True)

    # Closing Name
    closing_name = fields.Char("Closing Name", related="closing_contact.name",
                               store="True", tracking=True)

    # Closing Phone
    closing_phone = fields.Char("Closing Phone", related="closing_contact.phone",
                                store="True", tracking=True)

    # endregion

    # region Created SO / Sub

    sales_order = fields.One2many(
        "sale.order", "home_warranty", "Sales Orders")

    subscription = fields.One2many(
        "sale.subscription", "home_warranty", "Subscriptions")

    seller_order = fields.One2many('sale.order', "home_warranty", compute="_compute_orders",
                                   store=False, compute_sudo=True)

    buyer_order = fields.One2many('sale.order', "home_warranty", compute="_compute_orders",
                                  store=False, compute_sudo=True)

    sales_order_count = fields.Integer('Sales Order Count', compute="_compute_orders",
                                       store=False, compute_sudo=True)

    invoice_status_array = [
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('cancel', 'Cancelled'),
        ('done', 'Locked'),
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('open', 'Invoice Open'),
        ('posted', 'Invoice Posted'),
        ('paid', 'Invoice Paid'),
        ('to invoice', 'To Invoice')
    ]
    
    invoice_status = fields.Selection(invoice_status_array, string='Current Invoice Status', compute='_get_invoiced', store=True, readonly=True)

    seller_invoice_status = fields.Selection(invoice_status_array, string='Seller Invoice Status', compute='_get_invoiced', store=True, readonly=True)

    buyer_invoice_status = fields.Selection(invoice_status_array, string='Buyer Invoice Status', compute='_get_invoiced', store=True, readonly=True)

    @api.depends('sales_order', 'seller_contact', 'buyer_contact')
    def _compute_orders(self):
        for record in self.with_context(nolog=True):
            order_count = 0
            record.sales_order_count = order_count
            record.seller_order = False
            record.seller_mismatch = False
            record.buyer_order = False
            record.buyer_mismatch = False
            for order in record.sales_order:
                if order.order_type == 'Seller':
                    record.seller_order = order
                    record.seller_mismatch = (
                            record.seller_contact.id != order.partner_id.id)
                elif order.order_type in ['Buyer', 'Owner']:
                    record.buyer_order = order
                    record.buyer_mismatch = (
                            record.buyer_contact.id != order.partner_id.id)
                order_count = order_count + 1
            record.sales_order_count = order_count

    days_since_sub_start = fields.Integer(
        "Days Since Subscription Start Date", compute="_compute_days_since_subscription")

    def _compute_days_since_subscription(self):
        for record in self.with_context(nolog=True):
            sub = self.env['sale.subscription']
            sub = sub.search([['home_warranty', '=', record.id]])
            for s in sub:
                # try:
                #     if s.date_start > from_dt:
                #         from_dt = s.date_start
                # except:
                #     from_dt = s.date_start
                from_dt = s.date_start
                to_dt = datetime.strptime(fields.Date.today(), "%Y-%m-%d")
                timedelta = to_dt - from_dt
                record.days_since_sub_start = timedelta.days

    @api.depends('sales_order','buyer_order.invoice_ids.state','sales_order.invoice_ids.state')
    def _get_invoiced(self):
        self.sudo().with_context(nolog=True)._compute_orders()
        for record in self.sudo().with_context(nolog=True):
            if record.seller_order:
                if record.seller_order.invoice_status == 'no':
                    record.invoice_status = record.seller_order.state
                    record.seller_invoice_status = record.seller_order.state
                elif record.seller_order.invoice_status == 'invoiced':
                    if record.seller_order.invoice_ids[0].payment_state == 'paid':
                        state = 'paid'
                        # self.env['crm.lead'].update_hw_partner_lead_status(record.realtor_contact)
                    else:
                        state = 'open'
                    record.invoice_status = state
                    record.seller_invoice_status = state
                else:
                    record.invoice_status = record.seller_order.invoice_status
                    record.seller_invoice_status = record.seller_order.invoice_status
                for sub in record.seller_order.order_line.mapped('subscription_id'):
                    sub._get_last_payment()
            if record.buyer_order:
                if record.buyer_order.invoice_status == 'no':
                    record.invoice_status = record.buyer_order.state
                    record.buyer_invoice_status = record.buyer_order.state
                elif record.buyer_order.invoice_status == 'invoiced':
                    if record.buyer_order.invoice_ids[0].payment_state == 'paid':
                        state = 'paid'
                        # self.env['crm.lead'].update_hw_partner_lead_status(record.realtor_contact)
                    else:
                        state = 'open'
                    record.invoice_status = state
                    record.buyer_invoice_status = state
                else:
                    record.invoice_status = record.buyer_order.invoice_status
                    record.buyer_invoice_status = record.buyer_order.invoice_status
                for sub in record.buyer_order.order_line.mapped('subscription_id'):
                    sub._get_last_payment()

    # endregiocreate_owner_subscriptionn

    # region Product Line Items

    promo_code = fields.Char("Promo Code")

    promo = fields.Many2one("coupon.program", "Promo")

    promo_cost = fields.Float(related="promo.cost", store=True)

    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', tracking=1,
        help="If you change the pricelist, only newly added lines will be affected.")

    def get_product_id(rec, field, val, ids):
        id = []
        if rec[field]:
            id = rec.env['product.product'].search([
                ('warranty_term_id.name', '=', rec['covered_buyer_term']),
                ('name', '=ilike', val)])
            return ids + id
        return ids

    @api.depends('covered_buyer_term',
                 'property_type')
    def _compute_price_script(self):
        pricelist_obj = self.env['product.pricelist']
        res_country_state_obj = self.env['res.country.state']
        for rec in self.with_context(nolog=True):
            property_state_id = False
            if rec.property_state and rec.property_state.id:
                property_state_id = res_country_state_obj.browse(int(rec.property_state.id))
            pricelist_id = pricelist_obj.get_home_warranty_pricelist_by_state_wise(property_state_id)
            ps = "\n"
            ids = []
            if rec['property_state'] and rec['covered_sellers_coverage']:
                ids = self.env['product.product'].search(
                    [('warranty_consumer_id.name', '=', 'Seller')])

            if rec['covered_buyer_term']:
                if rec['covered_buyer_term'] == '48' or rec.covered_buyer_term == 'NC':
                    ids += rec.env['product.product'].search([
                        ('warranty_term_id.name', '=',
                         rec['covered_buyer_term']),
                        ('warranty_consumer_id.name', '=', 'Buyer')])
                else:
                    ids += rec.env['product.product'].search([
                        ('warranty_term_id.name', '=',
                         rec['covered_buyer_term']),
                        ('warranty_property_id.name',
                         '=', rec['property_type']),
                        ('warranty_consumer_id.name', '=', 'Buyer')])
                product_type_product_ids = rec.env['product.product'].search([
                    ('warranty_term_id.name', '=', rec['covered_buyer_term']),
                    ('warranty_consumer_id.name', '=', 'Buyer'),
                    ('sale_ok', '=', True),
                    ('attribute_line_ids.product_template_value_ids.product_attribute_value_id.term_product_type', '=',
                     'AddOn'), ('warranty_property_id.name', '=', rec['property_type'])])
                product_type_without_product_ids = rec.env['product.product'].search([
                    ('warranty_term_id.name', '=', rec['covered_buyer_term']),
                    ('warranty_consumer_id.name', '=', 'Buyer'),
                    ('sale_ok', '=', True),
                    ('attribute_line_ids.product_template_value_ids.product_attribute_value_id.term_product_type', '=',
                     'AddOn')]).filtered(lambda product_id: product_id.id not in product_type_product_ids.mapped('product_tmpl_id.product_variant_ids').ids)
                product_type_without_product_ids+=product_type_product_ids
                ids += product_type_without_product_ids
            _logger.info(f"Property State : {rec.property_state.id}, Home Warranty Pricelist : {pricelist_id}")
            for id in ids:
                for a in id.attribute_line_ids.product_template_value_ids.product_attribute_value_id:
                    if a.attribute_id.name == "Terms":
                        # ps += """$('#{0}_Price').html(" ${1:,.2f}"); //{2}\n """.format(
                        #     a.id, id.lst_price, id.name)
                        ps += """$('#{0}_Price').html(" ${1:,.2f}"); //{2}\n """.format(
                            a.id, id.with_context({'pricelist': pricelist_id}).price, id.name)

            rec.price_script = ps

    price_script = fields.Char('Price Script', compute='_compute_price_script')

    def get_product_price(rec, val):
        id = rec.env['product.product'].search([
            ('warranty_term_id.name', '=', rec['covered_buyer_term']),
            ('name', '=ilike', val),
            ('warranty_consumer_id.name', '=', 'Buyer')])
        return id

    def get_price_for_Portal(self, field, search):
        id = self.get_product_price(search)
        if id:
            return "$('#{0}_Price').html('${1:,.2f}');\n".format(field, id.list_price)
        return ""

    @api.depends('property_type')
    # add_on_filter Hack for Add on domain
    def _compute_add_on_filter(self):
        rental_addon_id = self.env['home.warranty'].sudo()._get_add_on_noop_attribute_value_id()
        for record in self:
            if record.property_type and record.property_type in ['Single Family Home', 'Townhome/Condo', 'New']:
                record.add_on_filter = 227
            else:
                record.add_on_filter = rental_addon_id

    add_on_filter = fields.Integer(
        "Addon Filter", compute='_compute_add_on_filter')

    conserve_add_on_filter = fields.Char("Conserve Addon Filter")

    @api.depends('product_seller',
                 'product_buyer')
    # Products
    def _compute_product(self):
        for record in self:
            ids = False
            try:
                ids = record.product_seller + record.product_buyer
            except Exception:
                _logger.log(logging.ERROR,
                            "Unable to calculate Products for %s" % record.id)

            record.product = ids

    product = fields.Many2many("product.product", compute='_compute_product')

    @api.depends('covered_seller_product_id',
                 'property_type',
                 'promo_code')
    # Products
    def compute_product_seller(self):
        for record in self:
            ids = False
            try:
                if record['covered_seller_product_id']:
                    if record.seller_order.state == 'done':
                        ids = record.seller_order.order_line.mapped(
                            'product_id').ids
                    else:
                        # if 'Advant' in seller_prod_name or 'Prime' in seller_prod_name:
                        if record['property_type']:
                            ids = self.env['product.product'].search(
                                [('warranty_terms_id', '=', record['covered_seller_product_id']['id']),
                                 ('warranty_property_id.name',
                                  '=', record['property_type']),
                                 ('warranty_consumer_id.name', '=', 'Seller')])
                        else:
                            ids = self.env['product.product'].search(
                                [('warranty_terms_id', '=', record['covered_seller_product_id']['id']),
                                 ('warranty_consumer_id.name', '=', 'Seller')])
            except Exception as e:
                _logger.log(
                    logging.ERROR, "Unable to calculate Seller Products for %s" % record.id)
                _logger.log(logging.ERROR, str(e))

            record.product_seller = ids

    product_seller = fields.Many2many(
        "product.product", compute='compute_product_seller')

    def _get_covered_buyer_addons_product_ids(self, attribute_value_id):
        if self.covered_owners_coverage:
            product_ids = self.env['product.product'].search(
                [('warranty_consumer_id.name', '=', 'Homeowner'), ('warranty_terms_id', '=', attribute_value_id),
                 ('renewal', '=', False)])
        else:
            product_ids = self.env['product.product'].search([('warranty_term_id.name', '=', self.covered_buyer_term),
                                                              ('warranty_terms_id', '=', attribute_value_id),
                                                              ('renewal', '=', False)])
        product_template_attribute_values_list = product_ids.product_template_attribute_value_ids.mapped('name')
        if product_template_attribute_values_list.__contains__(self.property_type):
            if self.covered_owners_coverage:
                product_ids = self.env['product.product'].search(
                    [('warranty_consumer_id.name', '=', 'Homeowner'), ('warranty_terms_id', '=', attribute_value_id),
                     ('warranty_property_id.name', '=', self.property_type), ('renewal', '=', False)])
            else:
                product_ids = self.env['product.product'].search(
                    [('warranty_term_id.name', '=', self.covered_buyer_term),
                     ('warranty_terms_id', '=', attribute_value_id),
                     ('warranty_property_id.name', '=', self.property_type), ('renewal', '=', False)])
        return product_ids

    @api.depends('covered_buyer_product_id',
                 'covered_owner_product_id',
                 'covered_buyer_term',
                 'property_type',
                 'pricelist_id',
                 'covered_buyer_addons',
                 'promo_code')
    # Products
    def compute_product_buyer(self):

        for record in self:
            ids = False
            product_attr_id = False
            try:
                if record.buyer_order.state == 'done':
                    ids = record.buyer_order.order_line.mapped(
                        'product_id').ids
                else:
                    # FIGURE OUT BASED ON CHECKBOX IN HW FORM
                    if record['covered_buyers_coverage']:
                        product_attr_id = record['covered_buyer_product_id']['id']
                    elif record['covered_owners_coverage']:
                        product_attr_id = record['covered_owner_product_id']['id']
                    elif record['covered_sellers_coverage'] and record['covered_buyer_product_id']:
                        product_attr_id = record['covered_buyer_product_id']['id']

                    if record['covered_buyer_term'] and product_attr_id and product_attr_id != 'False':
                        if record['covered_buyer_term'] == '48' or record.covered_buyer_term == 'NC':
                            ids = self.env['product.product'].search([
                                ('warranty_term_id.name', '=',
                                 record['covered_buyer_term']),
                                ('warranty_terms_id', '=', product_attr_id), ('renewal', '=', False)])
                        else:
                            # TODO test internal form to see if
                            # 'WARRANTY_TERMS_ID.ID' WORKS
                            ids = self.env['product.product'].search([
                                ('warranty_term_id.name', 'ilike',
                                 record['covered_buyer_term']),
                                ('warranty_terms_id.id', '=', product_attr_id),
                                ('warranty_property_id.name', '=', record['property_type']), ('renewal', '=', False)])
                        for p in record.covered_buyer_addons.ids:
                            ids += record._get_covered_buyer_addons_product_ids(attribute_value_id=p)

                        # PROMO COUPONS
                        if record.promo:
                            ids += record.promo.discount_line_product_id
                        elif record.promo_code and record.promo:
                            coupon_code = record.promo_code
                            program = self.env['coupon.program'].search(
                                [('promo_code', '=', record.promo_code)])
                            if program.maximum_use_number != 0 and program.order_count >= program.maximum_use_number:
                                msg = 'Promo code %s has been expired.' % coupon_code
                            elif program.rule_date_from and program.rule_date_from > datetime.now() or \
                                    program.rule_date_to and datetime.now() > program.rule_date_to:
                                msg = 'Promo code %s has been expired.' % coupon_code
                            else:
                                record.promo = program
                                ids += program.discount_line_product_id
            except Exception as e:
                _logger.log(
                    logging.ERROR, "Unable to calculate Buyer Products for %s" % record.id)
                _logger.log(logging.ERROR, str(e))
            record.product_buyer = ids

    product_buyer = fields.Many2many(
        "product.product", compute='compute_product_buyer')

    # endregion

    # region Actions

    def action_seller_order(self):
        """
        Create Seller Order and move status
        :return:
        """
        for rec in self:
            sales_id = rec.env.user.id
            if rec.realtor_contact.user_id:
                sales_id = rec.realtor_contact.user_id.id
            rec.sudo().with_context(
                {"sales_id": sales_id,
                 "user_id": rec.env.user.id,
                 "partner_id": rec.env.user.partner_id.id,
                 "validate": "no"}
            ).create_seller_subscription()
            rec.sudo().update_orders({})

    def action_buyer_order(self):
        """
        Create Buyer Order and move status
        :return:
        """
        for rec in self:
            sales_id = rec.env.user.id
            if rec.realtor_contact.user_id:
                sales_id = rec.realtor_contact.user_id.id
            rec.sudo().with_context(
                {"sales_id": sales_id,
                 "user_id": rec.env.user.id,
                 "partner_id": rec.env.user.partner_id.id,
                 "validate": "no"
                 }
            ).create_buyer_subscription()
            rec.sudo().update_orders({})

    def action_remove_coupon(self):
        """
        Remove promo
        :return:
        """
        for rec in self:
            rec.promo_code = False
            rec.promo = False
            self.compute_product_buyer()
            rec.update_orders([])
            # if rec.buyer_invoice_status in ['paid','cancel','invoiced']:
            # TODO: Warning

    def check_ready_for_subscription(self, sales_id=1, partner_id=1, user_id=1):
        """
        Check web form values for buyer subscription
        :return:
        """

        rec = self
        if rec.realtor_contact.user_id:
            sales_id = rec.realtor_contact.user_id.id
        context = \
            {"sales_id": sales_id,
             "nolog": True,
             "user_id": user_id,
             "partner_id": partner_id}

        msg = ""

        if rec.state == 'draft' and rec.covered_seller_product_id:
            rec.sudo().with_context(context).create_seller_subscription()

        if rec.state in ['Seller', 'draft'] and rec.covered_buyer_product_id and rec.covered_buyer_term:
            if rec.promo_code and not rec.promo:
                rec.promo_code = rec.promo_code.upper()
                program = self.env['coupon.program'].sudo().search(
                    [('promo_code', '=', rec.promo_code)])
                if not program:
                    rec.promo_code = False
                    return ['Promo %s not found' % rec.promo_code]
                error_status = program._check_hw_promo_code(
                    rec, rec.promo_code)
                if error_status.get('error'):
                    rec.promo_code = False
                    return error_status.get('error')
                else:
                    rec.promo = program
                    if program.discount_line_product_id not in rec.product:
                        rec.product += program.discount_line_product_id
                    return ['Promo %s Applied' % rec.promo_code]
            # try:
            rec.sudo().with_context(context).create_buyer_subscription()
            # except AttributeError as e:
            #    return ["Error Not Found", str(e)]

        return []

    def name_get(self):
        res = []
        for hw in self:
            name = hw.name or ''
            if self._context.get('show_address_only'):
                name = hw._display_address()
            if self._context.get('show_address'):
                name = name + "\n" + hw._display_address()
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((hw.id, name))
        return res

    def _display_address(self):
        if self.property_street and self.property_state:
            return str(self.property_street) + '\n' + \
                   str(self.property_city) + ', ' + \
                   str(self.property_state_code) + ' ' + str(self.property_zip)
        else:
            return ''

    @api.model
    def create(self, vals):
        """
        On new record assign name and status
        If record is from web form create subscriptions if data available
        :param vals:
        :return: bool - created
        """
        if vals.get('name') == "Web":
            vals['name'] = self.env['ir.sequence'].sudo().next_by_code(
                'home.warranty.seq') or '/'
            vals['state'] = 'draft'
            vals['submitter'] = self.env.user.id
            msg = ""
            rec = super(HomeWarranty, self).sudo().with_context(
                nolog=True).create(vals).with_context(nolog=True)
            if 'seller_name' in vals:
                rec['seller_name'] = vals['seller_name']
            if 'seller_email' in vals:
                rec['seller_email'] = vals['seller_email']
            if 'seller_phone' in vals:
                rec['seller_phone'] = vals['seller_phone']
            if 'buyer_name' in vals:
                rec['buyer_name'] = vals['buyer_name']
            if 'buyer_email' in vals:
                rec['buyer_email'] = vals['buyer_email']
            if 'buyer_phone' in vals:
                rec['buyer_phone'] = vals['buyer_phone']
            if 'paying_as' in vals:
                rec['paying_as'] = vals['paying_as']
            if rec['seller_name']:
                rec['seller_contact'] = rec.sudo().with_context(nolog=True).create_customer_contact(rec['seller_name'],
                                                                                                    rec['seller_email'],
                                                                                                    rec[
                                                                                                        'seller_phone']).id
            if rec['buyer_name']:
                if rec['paying_as'] == 'realtor':    
                    rec['buyer_contact'] = self.env.user.partner_id
                else:
                    rec['buyer_contact'] = rec.sudo().with_context(nolog=True).create_customer_contact(rec['buyer_name'],
                                                                                                    rec['buyer_email'],
                                                                                                    rec['buyer_phone']).id
            if 'closing_email' in vals and vals['closing_email'] != False:
                rec['closing_email'] = vals['closing_email']
                rec['closing_contact'] = rec.sudo().with_context(nolog=True).create_closing_contact(
                    rec['closing_email'])
            # rec.sudo().message_subscribe([1])
            if rec.realtor_salesperson.partner_id:
                rec.sudo().message_subscribe(
                    [rec.realtor_salesperson.partner_id.id])
            template = self.env.ref('achosa.hw_created')
            changes = []
            for key, val in vals.items():
                changes.append({'col_desc': key, 'new_value': val})
            template.sudo().with_context(
                {'tracking': changes, 'author': self.env.user.display_name}).send_mail(rec.id)
            return rec
        elif vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'home.warranty.seq') or '/'
            vals['state'] = 'draft'
            vals['submitter'] = self.env.user.id
            vals['message_follower_ids'] = []
            MailFollowers = self.env['mail.followers']
            # vals['message_follower_ids'] += MailFollowers._add_follower_command(self._name, [], {1: None}, {})[0]
            template = self.env.ref('achosa.hw_created')
            rec = super(HomeWarranty, self).sudo().create(vals)
            if rec.realtor_salesperson.partner_id:
                rec.sudo().message_subscribe(
                    [rec.realtor_salesperson.partner_id.id])
            changes = []
            for key, val in vals.items():
                changes.append({'col_desc': key, 'new_value': val})
            template.with_context({'tracking': changes, 'author': self.env.user.display_name, 'uid': self.env.user.id}) \
                .send_mail(rec.id)
            return rec

        return super(HomeWarranty, self).create(vals)

    def write(self, vals):
        """
        On record update: update sales orders if they exist
        :param vals:
        :return: bool - updated
        """
        res = super(HomeWarranty, self).write(vals)

        if (self._context.get('validate') or self._context.get('nolog')):
            return res

        self.update_orders(vals)

        return res

    def update(self, values):
        """ Update the records in ``self`` with ``values``. """
        for rec in self:
            for name, value in values.items():
                if rec['closing_email']:
                    rec['closing_contact'] = rec.sudo().with_context(
                        nolog=True).create_closing_contact(rec['closing_email'])
                rec[name] = value

    def update_orders(self, vals):

        # Update related models
        if self.seller_contact:
            seller = self.seller_contact.sudo()
            # if so update the address
            seller.street = self.property_street
            seller.street2 = self.property_street2
            seller.city = self.property_city
            seller.zip = self.property_zip
            seller.state_id = self.property_state.id
            seller.team_id = self.env['crm.team'].search(
                [('name', '=', 'Sales')], limit=1).id
        if self.sudo().seller_order and self.sudo().seller_order.state != 'done':
            # Update Seller Order
            so = self.sudo().seller_order
            subscriptions = so.order_line.mapped('subscription_id')
            if len(subscriptions) > 1:
                raise exceptions.Warning(_('Too many subscriptions on sales order. '
                                           'Please make sure there is only one subscription on the sales order. '
                                           'If there is Please delete all but one sales order lines. '
                                           '' + self.name))
            elif len(subscriptions) < 1:
                raise exceptions.Warning(_('Subscription not found on sales order. '
                                           'Please make sure there is a subscription on the sales order. '
                                           '' + self.name))
            so_products = []
            # Remove products no longer on order
            for line in so.order_line:
                if line.product_id.id not in self.product_seller.ids:
                    line.unlink()
                elif so_products.count(line.product_id.id) > 0:
                    raise exceptions.Warning(_('Duplicate products on sales order. '
                                               'Please delete all but one sales order lines.'
                                               '' + self.name))
                else:
                    so_products.append(line.product_id.id)
            # Add new products
            for product in self.product_seller:
                if so_products.count(product.id) < 1:
                    # Create the sales order lines
                    sales_order_line_obj = self.env['sale.order.line'].sudo()
                    sol_id = sales_order_line_obj.create({
                        "salesman_id": so.user_id.id,
                        "product_id": product.id,
                        "subscription_id": subscriptions[0].id,
                        "product_uom_qty": 1,
                        "discount": 0,
                        "order_id": so.id
                    }
                    )

        if self.buyer_contact:
            buyer = self.buyer_contact.sudo()
            # If so update the address
            buyer.street = self.property_street
            buyer.street2 = self.property_street2
            buyer.city = self.property_city
            buyer.zip = self.property_zip
            buyer.state_id = self.property_state.id
            buyer.team_id = self.env['crm.team'].search(
                [('name', '=', 'Sales')], limit=1).id
        if self.sudo().buyer_order and self.covered_buyer_product_id \
                and not self.covered_owners_coverage and self.sudo().buyer_order.state != 'done' \
                and not self._context.get('validate'):
            self.with_context(nolog=True).compute_product_buyer()
            # Update Buyer Order
            so = self.sudo().buyer_order
            subscriptions = so.order_line.mapped('subscription_id')
            if len(subscriptions) > 1:
                raise exceptions.Warning(_('Too many subscriptions on sales order. '
                                           'Please make sure there is only one subscription on the sales order. '
                                           'If there is Please delete all but one sales order lines.'
                                           '' + self.name))
            elif len(subscriptions) < 1:
                raise exceptions.Warning(_('Subscription not found on sales order. '
                                           'Please make sure there is a subscription on the sales order. '
                                           '' + self.name))
            so_products = []
            # Remove products no longer on order
            for line in so.order_line:
                if line.product_id.id not in self.product_buyer.ids:
                    line.unlink()
                elif so_products.count(line.product_id.id) > 0:
                    raise exceptions.Warning(_('Duplicate products on sales order. '
                                               'Please delete all but one sales order lines.'
                                               '' + self.name))
                else:
                    so_products.append(line.product_id.id)
            # Add new products
            for product in self.product_buyer:
                pid = product.id
                pname = product.name
                pcnt = so_products.count(product.id)
                if so_products.count(product.id) < 1:
                    # Create the sales order lines
                    sales_order_line_obj = self.env['sale.order.line'].sudo()
                    sol_id = sales_order_line_obj.create({
                        "salesman_id": so.user_id.id,
                        "product_id": product.id,
                        "subscription_id": subscriptions[0].id,
                        "product_uom_qty": 1,
                        "discount": 0,
                        "order_id": so.id
                    }
                    )
        _logger.log(logging.INFO, str(self.product_buyer))

        if self.realtor_contact:
            leads = self.env['crm.lead'].search(
                [['partner_id', '=', self.realtor_contact.id]])
            if leads:
                leads._get_count_hw()

        # make sure info@achosa.com is not following
        self.message_unsubscribe([1])

    # endregion

    def create_customer_contact(self, name, email, phone):
        """
        Using the information contained within the home warranty, create customer contact
        :param name:
        :param email:
        :param phone:
        :return: res.partner:  Created contact object
        """
        contact = self.env['res.partner']
        return contact.create({
            "name": name,
            "phone": phone,
            "email": email,
            "street": self.property_street,
            "street2": self.property_street2,
            "city": self.property_city,
            "zip": self.property_zip,
            "state_id": self.property_state.id,
            "team_id": self.env['crm.team'].search([('name', '=', 'Sales')], limit=1).id,
            "home_warranty": self.id
        })

    def update_customer_contact(self, contact, name, email, phone):
        """
        Using the information contained within the home warranty, create customer contact
        :param name:
        :param email:
        :param phone:
        :return: res.partner:  Created contact object
        """
        contact.name = name
        contact.phone = phone
        contact.email = email
        contact.street = self.property_street
        contact.street2 = self.property_street2
        contact.city = self.property_city
        contact.zip = self.property_zip
        contact.state_id = self.property_state.id
        contact.team_id = self.env['crm.team'].search(
            [('name', '=', 'Sales')], limit=1).id
        contact.home_warranty = self.id
        return contact.id

    def create_closing_contact(self, email):
        """
        Using the information contained within the home warranty, create customer contact
        :param email:
        :return: res.partner:  Created contact object
        """
        res_partner = self.env['res.partner']
        contact = res_partner.find_or_create(email)
        # contact["supplier"] = True // ODOO13 removed this field
        # contact["customer"] = False // ODOO13 removed this field
        contact["vendor_type"] = "Closing"
        return contact.id

    @staticmethod
    def get_subscription_template(products):
        """ Given a list of products, return the name of the subscription template

        Args:
          products:   Product list attached to this warranty

        Returns:
          str:        string of template id
        """
        for product in products:
            if product.subscription_template_id:
                return product.subscription_template_id

    def send_invoice(self, template_name, copy=False, author=False, template_id=False):
        """
        Portal Action to send invoice
        :param template_name: external id of the email template
        :return:
        """
        author_id = author or self.env.user.partner_id.id

        attachment_ids = []
        if 'seller' in template_name:
            for product in self.product_seller:
                for attr in product.attribute_line_ids.mapped('value_ids'):
                    attachments = self.env['ir.attachment'].sudo().search([
                        ('res_model', '=', 'product.attribute.value'),
                        ('res_id', '=', attr.id)])
                    for attach in attachments:
                        attachment_ids.append(attach.id)
        if 'buyer' in template_name:
            for product in self.product_buyer:
                for attr in product.attribute_line_ids.mapped('value_ids'):
                    attachments = self.env['ir.attachment'].sudo().search([
                        ('res_model', '=', 'product.attribute.value'),
                        ('res_id', '=', attr.id)])
                    for attach in attachments:
                        attachment_ids.append(attach.id)
        if template_id:
            self.sudo()._send_invoice(template_id, attachment_ids, author_id, copy)
        else:
            self.sudo()._send_invoice(template_name, attachment_ids, author_id, copy)

    def _send_invoice(self, template_name, attachment_ids, author_id, copy=False):
        """
        Send Invoice using email template
        :param template_name: external id of the email template
        :param attachment_ids: id of ir.attachments
        :param author_id: partner id that generated the email
        :return:
        """
        # Mail = self.env['mail.mail']
        if isinstance(template_name, int):
            template = self.env['mail.template'].browse(template_name)
        else:
            template = self.env.ref(template_name)

        mail_values = {
            'attachment_ids': [(4, id) for id in attachment_ids],
            'author_id': author_id
        }

        template.with_context({'copy': copy, 'coordinator': self._context.get('coordinator')}) \
            .send_mail(self.id, email_values=mail_values)

    def _validate_address_USPS(self):
        # TODO: config USERID
        if not self.property_state:
            return
        URL = ('http://production.shippingapis.com/ShippingAPITest.dll?API=Verify&XML=' +
               '<AddressValidateRequest USERID="546ANTIM6910"><Address ID="0">' +
               '<Address1>{0}</Address1>' +
               '<Address2>{1}</Address2>' +
               '<City>{2}</City>' +
               '<State>{3}</State>' +
               '<Zip5>{4}</Zip5>' +
               '<Zip4></Zip4></Address></AddressValidateRequest>') \
            .format(
            self.property_street, self.property_street2, self.property_city,
            self.property_state_code, self.property_zip
        )

        r = requests.get(url=URL)

        rxml = self.elem2dict(etree.XML(r.content))

        template = self.env.ref('achosa.hw_usps_address')
        template.sudo().with_context({'text': r.text, 'author': self.env.user.display_name, 'rxml': rxml}).send_mail(
            self.id)

        return

    def create_seller_subscription(self):
        """ Create a subscription and sales order based on the home warranty object

        """
        crm_lead_obj = self.env['crm.lead']
        if self.state == 'Seller' or self.state == 'Buyer':
            return False
        if self.realtor_salesperson.partner_id:
            self.sudo().message_subscribe(
                [self.realtor_salesperson.partner_id.id])

        # Confirm we have a seller contact
        if self.seller_contact:
            # if so update the address
            self.seller_contact.street = self.property_street
            self.seller_contact.street2 = self.property_street2
            self.seller_contact.city = self.property_city
            self.seller_contact.zip = self.property_zip
            self.seller_contact.state_id = self.property_state.id
            self.seller_contact.team_id = self.env['crm.team'].search(
                [('name', '=', 'Sales')], limit=1).id
        else:
            # if not create or return false
            if self.seller_name:
                self.seller_contact = self.create_customer_contact(self.seller_name, self.seller_email,
                                                                   self.seller_phone).id
            else:
                return False

        # self._validate_address_USPS()

        # The following is a bit of a hack to get the template information for
        # the subscription creation
        subscription_obj = self.env['sale.subscription']
        template = self.get_subscription_template(self.product_seller)
        recurring_next_date = subscription_obj._get_recurring_next_date(template.recurring_rule_type,
                                                                        template.recurring_interval,
                                                                        datetime.today(), datetime.today().day)
        end_date = fields.Date.from_string(recurring_next_date) - relativedelta(days=1)
        pricelist_id = self.env['product.pricelist'].get_home_warranty_pricelist_by_state_wise(self.property_state)
        # Create the subscription object
        created_sub_obj = subscription_obj.create(
            {
                'user_id': self._context["sales_id"] or self.user_id.id,
                "partner_id": self.seller_contact.id,
                "pricelist_id": pricelist_id,
                # "x_housing_type": self.property_type,
                "template_id": template.id,
                # "x_hw_ref": self.name,
                "home_warranty": self.id,
                "submitter": self._context["user_id"] or self.user_id.id,
                "recurring_next_date": recurring_next_date,
                "date": end_date
            }
        )
        created_sub_obj.start_subscription()
        _logger.info(
            f"Subscription: [{created_sub_obj.name}] Date of Next Invoice: [{recurring_next_date.strftime('%m/%d/%Y') if recurring_next_date else ''}, End Date: [{end_date.strftime('%m/%d/%Y') if end_date else ''}]]")

        # Create the sales order object
        sales_order_obj = self.env['sale.order']
        
        partner_id = self.seller_contact.id
        for i in self.seller_contact.child_ids:
            if i.type == "invoice":
                partner_id = i.id
                

        created_sales_order_obj = sales_order_obj.create({
            'user_id': self._context["sales_id"] or self.user_id.id,
            "partner_id": partner_id,
            "state": "sent",
            'pricelist_id': pricelist_id,
            "home_warranty": self.id,
            "submitter": self._context["user_id"] or self.user_id.id,
            "order_type": "Seller"
        })
        # Create the sales order lines
        sales_order_line_obj = self.env['sale.order.line']
        sales_order_lines_id = []
        attachment_ids = []
        for product in self.product_seller:
            sol_id = sales_order_line_obj.create({
                "salesman_id": self._context["sales_id"] or self.user_id.id,
                "product_id": product.id,
                "subscription_id": created_sub_obj.id,
                "product_uom_qty": 1,
                "discount": 0,
                "order_id": created_sales_order_obj.id
            }
            )
            for attr in product.attribute_line_ids.mapped('value_ids'):
                attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', 'product.attribute.value'),
                    ('res_id', '=', attr.id)])
                for attach in attachments:
                    attachment_ids.append(attach.id)

            sales_order_lines_id.append(sol_id)

        # var to lookup template name by product
        # p = self.product_seller_template
        p = 'achosa.seller_basic_Seller'
        if self.covered_seller_product_id.seller_seller_email_template:
            p = self.covered_seller_product_id.seller_seller_email_template.id

        if self.seller_email:
            self._send_invoice(p, attachment_ids,
                               self._context["partner_id"] or self.user_id.id)

        p = 'achosa.seller_basic_Realtor'
        if self.covered_seller_product_id.seller_realtor_email_template:
            p = self.covered_seller_product_id.seller_realtor_email_template.id

        self.with_context({'coordinator': True})._send_invoice(p, attachment_ids,
                                                               self._context["partner_id"] or self.user_id.id)

        realtor_contact = self.realtor_contact
        if realtor_contact:
            lead_ids = crm_lead_obj.get_hw_partner_lead_ids(realtor_contact)
            if not lead_ids:
                user_id = self._context["sales_id"] or ""#self.user_id.id
                crm_lead_obj.create_hw_lead(self, realtor_contact, user_id=user_id)
            for lead_id in lead_ids:
                lead_id._update_hw_lead_status(realtor_contact)
        self.state = 'Seller'

    @api.onchange('estimated_closing_date')
    def _onchange_check_estimated_date(self):
        if self.estimated_closing_date:
            estimated_before = datetime.now().date() + relativedelta(days=-7)
            if self.estimated_closing_date < estimated_before:
                return {
                    'warning': {
                        'title': _('Warning'),
                        'message': _(
                            'The Estimated Closing Date cannot be more than before 7 days from Today’s Date.')
                    }
                }

    def create_buyer_subscription(self):
        """ Create a subscription and sales order based on the home warranty object

        """
        crm_lead_obj = self.env['crm.lead']
        if self.state == 'Buyer':
            return False

        if self.estimated_closing_date and not self.env.user.has_group('achosa.group_hw_admin'):
            estimated_before = datetime.now().date() + relativedelta(days=-7)
            if self.estimated_closing_date < estimated_before:
                raise ValidationError(
                    _('The Estimated Closing Date cannot be more than before 7 days from Today’s Date.'))

        # if self.estimated_closing_date and self.estimated_closing_date < fields.Date.today() and not self.env.user.has_group('achosa.group_hw_admin'):
        # raise ValidationError(_('The Estimated Closing Date cannot be before Today’s Date.'))

        # if self.estimated_closing_date:
        #    estimated_before = datetime.now().date() + \
        #        relativedelta(days=-7)
        #    if self.estimated_closing_date < estimated_before:
        #        raise ValidationError(
        #            _('The Estimated Closing Date cannot be more than before 7 days from Today’s Date.'))

        if self.realtor_salesperson.partner_id:
            self.sudo().message_subscribe(
                [self.realtor_salesperson.partner_id.id])

        # if self.property_type == 'New' and self.covered_buyer_term != '48':
        #     self.sudo().covered_buyer_term = '48'

        # Confirm we have a buyer contact
        if self.buyer_contact:
            if self.paying_as != 'realtor':
                # If so update the address
                self.buyer_contact.street = self.property_street
                self.buyer_contact.street2 = self.property_street2
                self.buyer_contact.city = self.property_city
                self.buyer_contact.zip = self.property_zip
                self.buyer_contact.state_id = self.property_state.id
                self.buyer_contact.team_id = self.env['crm.team'].search(
                    [('name', '=', 'Sales')], limit=1).id
        else:
            if self.buyer_name:
                self.buyer_contact = self.create_customer_contact(self.buyer_name, self.buyer_email,
                                                                  self.buyer_phone).id
            else:
                return False

        # self._validate_address_USPS()

        # The following is a bit of a hack to get the template information for
        # the subscription creation
        subscription_obj = self.env['sale.subscription']
        template = self.get_subscription_template(self.product_buyer)
        if not template:
            return False

        recurring_next_date = subscription_obj._get_recurring_next_date(template.recurring_rule_type,
                                                                        template.recurring_interval,
                                                                        datetime.today(), datetime.today().day)
        # end_date = fields.Date.from_string(recurring_next_date) - relativedelta(days=1)
        end_date = False
        pricelist_id = self.env['product.pricelist'].get_home_warranty_pricelist_by_state_wise(self.property_state)
        # Create the subscription object
        created_sub_obj = subscription_obj.create(
            {
                'user_id': self._context["sales_id"] or self.user_id.id,
                "partner_id": self.buyer_contact.id,
                "pricelist_id": pricelist_id,
                # "x_housing_type": self.property_type,
                "template_id": template.id,
                # "x_hw_ref": self.name,
                "home_warranty": self.id,
                "submitter": self._context["user_id"] or self.user_id.id,
                "recurring_next_date": recurring_next_date,
                "date": end_date
            }
        )
        _logger.info(
            f"Subscription: [{created_sub_obj.name}] Date of Next Invoice: [{recurring_next_date.strftime('%m/%d/%Y') if recurring_next_date else ''}, End Date: [{end_date.strftime('%m/%d/%Y') if end_date else ''}]]")
        # Create the sales order object
        sales_order_obj = self.env['sale.order']
        
        partner_id = self.buyer_contact.id
        for i in self.buyer_contact.child_ids:
            if i.type == "invoice":
                partner_id = i.id

        created_sales_order_obj = sales_order_obj.create({
            'user_id': self._context["sales_id"] or self.user_id.id,
            "partner_id": partner_id,
            "state": "sent",
            "pricelist_id": pricelist_id,
            "home_warranty": self.id,
            "submitter": self._context["user_id"] or self.user_id.id,
            "order_type": "Buyer"
        })

        # Create the sales order lines
        sales_order_line_obj = self.env['sale.order.line']
        sales_order_lines_id = []
        attachment_ids = []
        self.compute_product_buyer()
        for product in self.product_buyer:
            sol_id = sales_order_line_obj.create({
                "salesman_id": self._context["sales_id"] or self.user_id.id,
                "product_id": product.id,
                "subscription_id": created_sub_obj.id,
                "product_uom_qty": 1,
                "discount": 0,
                "order_id": created_sales_order_obj.id
            }
            )
            for attr in product.attribute_line_ids.mapped('value_ids'):
                attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', 'product.attribute.value'),
                    ('res_id', '=', attr.id)])
                for attach in attachments:
                    attachment_ids.append(attach.id)

            # Handle -$1mil discount default
            if sol_id.price_unit < -10000:
                sol_id.price_unit = 0

            if sol_id.related_program:
                sol_id.is_reward_line = True
                created_sales_order_obj.code_promo_program_id = sol_id.related_program

            sales_order_lines_id.append(sol_id)

        realtor_contact = self.realtor_contact
        if realtor_contact:
            lead_ids = crm_lead_obj.get_hw_partner_lead_ids(realtor_contact)
            if not lead_ids:
                user_id = self._context["sales_id"] or ""#self.user_id.id
                crm_lead_obj.create_hw_lead(self, realtor_contact, user_id=user_id)
            for lead_id in lead_ids:
                lead_id._update_hw_lead_status(realtor_contact)
        self.state = 'Buyer'

        # If buyer email send notification to seller using template "Buyers
        # Order - Buyer"
        if self.buyer_email:
            # TODO fix template render error
            self._send_invoice('achosa.buyer_all_buyer', attachment_ids[:],
                               self._context["partner_id"] or self.user_id.id)

        # Send notification to Realtor using template "Buyers Order - Realtor"
        self.with_context({'coordinator': True})._send_invoice('achosa.buyer_all_realtor', attachment_ids[:],
                                                               self._context["partner_id"] or self.user_id.id)

        # If closing email send notification to seller using template "Buyers
        # Order - Closing"
        if self.closing_email:
            self._send_invoice('achosa.buyer_all_closing', attachment_ids[:],
                               self._context["partner_id"] or self.user_id.id)
            
    def update_fix_renewal_products(self):
        for sub in self:
            reference = False
            for product in sub.recurring_invoice_line_ids.mapped('product_id'):
              if "-SFH" in product.default_code or "-S" in product.default_code:
                reference = "-S"
              elif "-TORC" in product.default_code or "-C" in product.default_code:
                reference = "-C"
              elif "-DUP" in product.default_code or "-2" in product.default_code:
                reference = "-2"
              elif "-TRI" in product.default_code or "-3" in product.default_code:
                reference = "-3"
              elif "-FOUR" in product.default_code or "-4" in product.default_code:
                reference = "-4"

            old_product = False
            new_product = False
            for product in sub.recurring_invoice_line_ids.mapped('product_id'):
              if ("conserve" in product.name.lower() or "non-owner-occupied" in product.name.lower()) and "-d2c" in product.default_code.lower():
                new_default_code = product.default_code.replace("-D2C", reference)
                new_product = self.env['product.product'].search([('default_code', '=', new_default_code)])
                old_product = product

            if old_product and new_product:
              # try:
              #   sub.write({'recurring_invoice_line_ids': [(3, old_product.id)]})
              # except Exception as e:
              #   message += str(e) + "\n"
              sub.write({'recurring_invoice_line_ids': [(0, 0, {'name': new_product.name, 'product_id': new_product.id, 'quantity': 1, 'price_unit': new_product.lst_price, 'uom_id': new_product.uom_id.id})]})

    def create_owner_subscription(self, start_date=datetime.today(), old_sub=False, mail_template=False):
        """ Create a subscription and sales order based on the home warranty object
        """
        # print(self.name)
        crm_lead_obj = self.env['crm.lead']
        if self.state == 'Owner':
            return False
        if self.realtor_salesperson.partner_id:
            self.sudo().with_context({'validate': True}).message_subscribe(
                [self.realtor_salesperson.partner_id.id])

        # if self.property_type == 'New' and self.covered_buyer_term != '48':
        #    self.sudo().covered_buyer_term = '48'

        # Confirm we have a buyer contact
        if not self.buyer_contact:
            # If so update the address
            # self.buyer_contact.street = self.property_street
            # self.buyer_contact.street2 = self.property_street2
            # self.buyer_contact.city = self.property_city
            # self.buyer_contact.zip = self.property_zip
            # self.buyer_contact.state_id = self.property_state.id
            # self.buyer_contact.team_id = self.env['crm.team'].search([('name', '=', 'Sales')], limit=1).id
            # else:
            if self.buyer_name:
                self.buyer_contact = self.create_customer_contact(self.buyer_name, self.buyer_email,
                                                                  self.buyer_phone).id
            else:
                return False

        products = self.env['product.product']
        if old_sub:
            for product in old_sub.recurring_invoice_line_ids.mapped('product_id'):
                if product.renewal_product:
                    products += product.renewal_product
        else:
            products = self.product_buyer

        # self._validate_address_USPS()

        # The following is a bit of a hack to get the template information for the subscription creation
        # subscription_obj = self.env['sale.subscription']
        # template = self.get_subscription_template(products)

        # Create the subscription object
        # created_sub_obj = subscription_obj.create(
        #     {
        #         'user_id': self._context.get("sales_id") or self.realtor_contact.user_id.id,
        #         "partner_id": self.buyer_contact.id,
        #         "pricelist_id": self.buyer_contact.property_product_pricelist.id,
        #         # "x_housing_type": self.property_type,
        #         "template_id": template.id,
        #         "x_hw_ref": self.name,
        #         "home_warranty": self.id,
        #         "submitter": self._context.get("user_id") or self.env.user.id,
        #         "recurring_next_date": start_date + relativedelta(months=1),
        #         "date": start_date + relativedelta(months=1),
        #         "date_start": start_date
        #     }
        # )

        # Create the sales order object
        sales_order_obj = self.env['sale.order']

        partner_id = self.buyer_contact.id
        for i in self.buyer_contact.child_ids:
            if i.type == "invoice":
                partner_id = i.id

        created_sales_order_obj = sales_order_obj.create({
            'user_id': self._context.get("sales_id") or self.realtor_contact.user_id.id,
            "partner_id": partner_id,
            "state": "sent",
            "home_warranty": self.id,
            "submitter": self._context.get("user_id") or self.env.user.id,
            "order_type": "Owner",
            "subscription_start_date": start_date
        })

        if old_sub:
            pricelist = self.env['product.pricelist'].search(
                [('name', 'like', 'Renewal%')])
            if len(pricelist.ids) > 0:
                created_sales_order_obj.pricelist_id = pricelist[0].id
                # created_sub_obj.pricelist_id = pricelist[0].id

        # Create the sales order lines
        sales_order_line_obj = self.env['sale.order.line']
        sales_order_lines_id = []
        attachment_ids = []
        product_category_id = self.env['product.category'].search([('name', '=ilike', 'Home Warranties')], limit=1)
        product_adddon_category_id = self.env['product.category'].search([('name', '=ilike', 'Add-Ons')], limit=1)
        home_warranty_product_id = products.filtered(
            lambda product_id: product_id.categ_id.id == product_category_id.id)

        for product in products:
            sol_id = sales_order_line_obj.create({
                "salesman_id": self._context["sales_id"] or self.realtor_contact.user_id.id,
                "product_id": product.find_property_type_product(
                    home_warranty_product_id).id if product.categ_id.id == product_adddon_category_id.id else product.id,
                # "subscription_id": created_sub_obj.id,
                "product_uom_qty": 1,
                "discount": 0,
                "order_id": created_sales_order_obj.id
            }
            )
            for attr in product.attribute_line_ids.mapped('value_ids'):
                attachments = self.env['ir.attachment'].search([
                    ('res_model', '=', 'product.attribute.value'),
                    ('res_id', '=', attr.id), ('public','=',True)])
                for attach in attachments:
                    attachment_ids.append(attach.id)

            # Handle -$1mil discount default
            if sol_id.price_unit < -10000:
                sol_id.price_unit = 0

            if sol_id.related_program:
                sol_id.is_reward_line = True
                created_sales_order_obj.code_promo_program_id = sol_id.related_program

            sales_order_lines_id.append(sol_id)

        realtor_contact = self.realtor_contact
        if realtor_contact:
            lead_ids = crm_lead_obj.get_hw_partner_lead_ids(realtor_contact)
            if not lead_ids:
                user_id = self._context["sales_id"] or ""#self.user_id.id
                crm_lead_obj.create_hw_lead(self, realtor_contact, user_id=user_id)
            for lead_id in lead_ids:
                lead_id._update_hw_lead_status(realtor_contact)
        self.state = 'Owner'

        # If buyer email send notification to seller using template "Buyers
        # Order - Buyer"
        if self.buyer_email:
            if old_sub:
                created_sales_order_obj.state = 'sent'
                if mail_template:
                    template = mail_template
                else:
                    template = self.env.ref('achosa.email_template_edi_sale')
                template.send_mail(created_sales_order_obj.id,
                                   email_values={'attachment_ids': [(4, id) for id in attachment_ids],
                                                 'author_id': self._context.get("partner_id") or
                                                              self.env.user.id})
            else:
                self._send_invoice('achosa.buyer_all_buyer', attachment_ids[:],
                                   self._context.get("partner_id") or self.env.user.id)

    # def message_track(self, tracked_fields, initial_values):
    #     """ Track updated values. Comparing the initial and current values of
    #     the fields given in tracked_fields, it generates a message containing
    #     the updated values. """
    #     tracking = dict()
    #
    #     if not tracked_fields:
    #         return tracking
    #
    #     for record in self:
    #         changes = set()  # contains onchange tracked fields that changed
    #         tracking_value_ids = []
    #         # prevent multiple emails on creation
    #         if not record._context.get('nolog'):
    #             initial = initial_values[record.id]
    #             for col_name, col_info in tracked_fields.items():
    #                 initial_value = initial[col_name]
    #                 new_value = self[col_name]
    #                 if new_value != initial_value and (new_value or initial_value):
    #                     if col_info['type'] != 'boolean':
    #                         if not initial_value:
    #                             initial_value = ''
    #                         if not new_value:
    #                             new_value = ''
    #                     tracking_sequence = getattr(self._fields[col_name], 'tracking',
    #                                                 getattr(self._fields[col_name], 'track_sequence',
    #                                                         100))  # backward compatibility with old parameter name
    #                     if tracking_sequence is True:
    #                         tracking_sequence = 100
    #                     track_rec = self.env['mail.tracking.value'].create_tracking_values(
    #                         initial_value, new_value, col_name, col_info, tracking_sequence)
    #                     if tracking:
    #                         tracking_value_ids.append([0, 0, track_rec])
    #                     changes.add(col_name)
    #             if len(changes) > 0:
    #                 template = self.env.ref('achosa.hw_updated')
    #                 template.with_context({'tracking': changes, 'author': self.env.user.display_name}).send_mail(
    #                     record.id)
    #         tracking[record.id] = changes, tracking_value_ids
    #
    #     return tracking

    def action_view_seller_order(self):
        """
        Open Seller Order
        :return:
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[self.env.ref('sale.view_order_form').id, "form"], [False, "tree"],
                      [False, "kanban"], [False, "calendar"], [False, "pivot"], [False, "graph"]],
            "res_id": self.seller_order.id,
            "context": {"create": False},
            "name": _("Sales Orders"),
        }

    def action_view_buyer_order(self):
        """
        Open Seller Order
        :return:
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[self.env.ref('sale.view_order_form').id, "form"], [False, "tree"],
                      [False, "kanban"], [False, "calendar"], [False, "pivot"], [False, "graph"]],
            "res_id": self.buyer_order.id,
            "context": {"create": False},
            "name": _("Sales Orders"),
        }

    def action_view_sales_orders(self):
        """
        Open Seller Order
        :return:
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[self.env.ref('sale_subscription.sale_order_view_tree_subscription').id, "tree"],
                      [self.env.ref('sale.view_order_form').id, "form"],
                      [False, "kanban"], [False, "calendar"], [False, "pivot"], [False, "graph"]],
            "domain": [["id", "in", self.sales_order.ids]],
            "context": {"create": False},
            "name": _("Sales Orders"),
        }

    @api.onchange('property_state')
    def change_property_state(self):
        s = self.sudo().with_context(nolog=True)
        s.covered_seller_product_id = False
        s.covered_buyer_product_id = False
        pricelist_id = self.env['product.pricelist'].get_home_warranty_pricelist_by_state_wise(self.property_state)
        values = {'covered_seller_product_id': False,
                  'covered_buyer_product_id': False,
                  'pricelist_id': pricelist_id}
        return {'value': values}

    # @api.onchange('property_type')
    # def change_property_type(self):
    #     if self.property_type == 'New' and self.covered_buyer_term != '48':
    #         self.sudo().with_context(nolog=True).covered_buyer_term = '48'

    # @api.onchange('covered_buyer_term')
    # def change_covered_buyer_term(self):
    #     if self.covered_buyer_term == '48' and self.property_type != 'New':
    #         self.sudo().with_context(nolog=True).property_type == 'New'

    @api.onchange('realtor_email', 'buyer_email', 'seller_email', 'closing_email')
    def validate_email(self):
        for record in self:
            if record.realtor_email and self.invalid_email_inlist(record.realtor_email):
                raise UserError('Invalid Realtor Email')
            if record.buyer_email and self.invalid_email_inlist(record.buyer_email):
                raise UserError('Invalid Buyer Email')
            if record.seller_email and self.invalid_email_inlist(record.seller_email):
                raise UserError('Invalid Seller Email')
            if record.closing_email and self.invalid_email_inlist(record.closing_email):
                raise UserError('Invalid Closing Email')

    @staticmethod
    def invalid_email_inlist(email):
        for e in email.replace(';', ',').split(','):
            if not tools.single_email_re.match(e.strip()):
                return True
        return False

    def elem2dict(self, node):
        """
        Convert an lxml.etree node tree into a dict.
        """
        result = {}

        for element in node.iterchildren():
            # Remove namespace prefix
            key = element.tag.split(
                '}')[1] if '}' in element.tag else element.tag

            # Process element as tree element if the inner XML contains
            # non-whitespace content
            if element.text and element.text.strip():
                value = element.text
            else:
                value = self.elem2dict(element)

            result[key] = value

        return result

    def confirm_seller(self):
        """
        Apply the check received if valid, raise an UserError otherwise.
        """
        for home_warranty in self:
            home_warranty._get_invoiced()
            # Confirm and create invoice
            so = home_warranty.seller_order
            if so:
                if self.realtor_salesperson:
                    so.user_id = home_warranty.realtor_salesperson
                if so.state == 'cancel':
                    return {'warning': {'title': _("Warning"), 'message': "Cancelled - " + so.name}}
                if not so.state == 'done':
                    so.action_confirm()
                if not so.invoice_ids:
                    so._create_invoices()
                inv = so.invoice_ids
                if len(inv.ids) < 1:
                    return {'warning': {'title': _("Warning"), 'message': "No invoice - " + so.name}}
                if len(inv.ids) != 1:
                    return {'warning': {'title': _("Warning"), 'message': "Too Many invoices - " + so.name}}
                if inv.state != 'draft':
                    home_warranty._get_invoiced()
                    return {'warning': {'title': _("Warning"), 'message': "Already invoiced - " + inv.name}}
                inv.write({'is_move_sent': True})
                if inv.state == 'draft':
                    inv.post()
                if self.realtor_salesperson:
                    inv.user_id = home_warranty.realtor_salesperson
                # Start Subscription
                sub = so.order_line.mapped(
                    'invoice_lines').mapped('subscription_id')
                if sub:
                    sub.set_open()
                    sub.date_start = fields.Date.today()
                    # set end date
                    sub.date = fields.Date.from_string(
                        sub.date_start) + relativedelta(months=6) - relativedelta(days=1)
                    sub.recurring_next_date = False

                home_warranty._get_invoiced()

            # Return
            return True

    @api.onchange('rental_property')
    def _onchange_rental_property(self):
        for r in self:
            attr = self.env["product.attribute.value"].browse(
                [r.rental_addon_id])
            if r.property_state not in attr.states:
                r.rental_property = "False"
            if r.rental_property == "True":
                if r.rental_addon_id not in r.covered_buyer_addons.ids:
                    r['covered_buyer_addons'] += attr
            else:
                r['covered_buyer_addons'] = [(3, attr.id)]

    @api.onchange('covered_buyer_addons')
    def _onchange_covered_buyer_addons(self):
        for r in self:
            if r.rental_addon_id in r.covered_buyer_addons.ids:
                r.rental_property = "True"
            else:
                r.rental_property = "False"

            if r.conserve_id in r.covered_buyer_addons.ids:
                r.conserve_add_on_filter = r.conserve_plus_id
            elif r.conserve_plus_id in r.covered_buyer_addons.ids:
                r.conserve_add_on_filter = r.conserve_id
            else:
                r.conserve_add_on_filter = False

    @api.onchange('property_state')
    def _onchange_property_state(self):
        for l in self:
            attr = self.env["product.attribute.value"].browse(
                [l.rental_addon_id])
            if l.property_state not in attr.states:
                l.hide_rental_property = True
                l.rental_property = "False"
            else:
                l.hide_rental_property = False

    @api.onchange('property_state')
    def _update_property_state(self):
        for l in self:
            l.property_state_code = self.env['res.country.state'].search(
                [('id', '=', l.property_state.id)]).code

    def _get_add_on_attribute_value_id(self):
        company_id = self.env.company
        conserve_id = company_id.add_on_attribute_value_conserve
        conserve_plus_id = company_id.add_on_attribute_value_conserve_plus
        _logger.info(
            f"Company: [{company_id and company_id.name}], "
            f"Conserve Attribute Value Id: [{conserve_id}], Conserve Plus Attribute Value Id: [{conserve_plus_id}]")
        return conserve_id, conserve_plus_id

    def _get_add_on_noop_attribute_value_id(self):
        company_id = self.env.company
        rental_addon_id = company_id.add_on_attribute_value_non_owner
        _logger.info(f"Company: [{company_id and company_id.name}], Rental Addon: [{rental_addon_id}]")
        return rental_addon_id

    def _compute_addon_id(self):
        conserve_id, conserve_plus_id = self._get_add_on_attribute_value_id()
        rental_addon_id = self._get_add_on_noop_attribute_value_id()
        self.rental_addon_id = rental_addon_id
        self.conserve_id = conserve_id
        self.conserve_plus_id = conserve_plus_id
        self.non_owner_addon_id = 227

    @api.onchange('closing_contact')
    def _update_closing_email(self):
        self.closing_email = self.closing_contact.email

    @api.onchange('closing_email')
    def _incorrect_email_alert(self):
        if self.closing_contact.email not in [None, '', False] and self.closing_email != self.closing_contact.email:
            message = _(
                'You are adding an email for the closing agent that is different from what is on their contact record. '
                'Please make sure the email is correct. '
                '' + str(self.closing_contact.email))
            warn = {
                'title': _('Possible Email Issue'),
                'message': message
            }
            return {'warning': warn}

    # @api.onchange('covered_owners_coverage')
    # def _update_realtor(self):
    #     if self.covered_owners_coverage == True:
    #         ecomm_realtor = self.env['res.partner'].search([('id','=','194628')])[0]
    #         self.realtor_contact = ecomm_realtor

    def copy(self, default=None):
        """
            @Usage: Puted the restrictions, only those users are able to duplicate the home warranty
            whose are available in the 'Administration / Settings' group
            Ticket: [AO-798]
        """
        if self.env.user.has_group('base.group_system'):
            default = default or {}
            res = super(HomeWarranty, self).copy(default)
            return res
        raise UserError(
            _("You haven't access right to duplicate the home warranty! Please contact your administrator."))

    def get_realtor_home_warranty_ids(self, partner_id):
        return self.search([('realtor_contact', '=', partner_id.id)])

    # Update this function when non-int selection is added to covered_buyer_term field
    def get_covered_term_id(self):
        if self.covered_buyer_term == 'NC':
            covered_buyer_term = 48
        else:
            covered_buyer_term = int(self.covered_buyer_term)
        return covered_buyer_term

