import logging
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import time
from odoo.exceptions import UserError

import json

_logger = logging.getLogger("##### Achosa #####")


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    def _get_salesperson_domain(self):
        team_id = self.env.ref('sales_team.team_sales_department', raise_if_not_found=False)
        # return [('groups_id', 'in', self.env.ref('base.group_user').id),
        #         ('sale_team_id', '=', team_id.id if team_id else False)]
        return [('sale_team_id', '=', team_id.id if team_id else False)]
    
    def create_expired_sub_activity(self):
        """
           This method will create activities on the given sub depending on how expired the sub is
            :return: None
        """
        recent_date = False
        users = self.env['res.users']
        sales = self.env['sale.order']
        sale_rep_id = False
        online_sales = users.search([('login', '=', 'sales@achosahw.com')])
        corey_id = users.search([('login', '=', 'coreys@achosahw.com')])
        stacy_id = users.search([('login', '=', 'stacys@achosahw.com')])
        sale_rep_dict = {corey_id: ['AR','SC','WV','IN','OK','MS','MD','IA','ID','MI','VA','GA','TN','KS','OH','KY'],
                         stacy_id: ['TX', 'IL', 'MO', 'AL', 'NC', 'PA', 'NV']}
        for sub in self:
            order = False
            orders = sales.search([('subscriptions', 'in', [sub.id])])
            # orders = sub.home_warranty.sales_order
            if sub.home_warranty.property_state.code in sale_rep_dict[corey_id]:
                sale_rep_id = corey_id.id
            elif sub.home_warranty.property_state.code in sale_rep_dict[stacy_id]:
                sale_rep_id = stacy_id.id
            else:
                sale_rep_id = online_sales.id

            if len(orders) > 1:    
                for o in orders:
                    if not recent_date:
                        recent_date = o.date_order
                    elif o.date_order < recent_date:
                        recent_date = o.date_order
                    else:
                        if o.state == 'done':
                            o.action_unlock()
                        order = o
            else:
                order = orders
            
            if order:
                todos = {'res_id': order.id,
                            'res_model_id': self.env['ir.model'].search([('model', '=', 'sale.order')]).id,
                            'user_id': sale_rep_id,
                            'summary': "1st Touch",
                            'note': 'Reach out to customer to renew sub and create follow-up activity',
                            'activity_type_id': 4,
                            'date_deadline': datetime.today(),
                                }
                _logger.info(todos)
                self.env['mail.activity'].create(todos)


    def _get_expiry_code(self):
        for sub in self:
            if sub.to_renew:
                today = datetime.today().date()
                tDate = sub.recurring_next_date if sub.recurring_next_date else today
                tDelta8 = today - timedelta(days=8)
                tDelta30 = today - timedelta(days=30)
                    
                if tDate < today and tDate >= tDelta8:
                    #PAST DUE
                    sub.sudo().write({"sub_expiry_code": "P"})
                elif tDate > tDelta30 and tDate < tDelta8:
                    #AT RISK
                    sub.create_expired_sub_activity()
                    sub.sudo().write({"sub_expiry_code": "R"})
                elif tDate < tDelta30:
                    #DEAD SUB
                    sub.sudo().write({"sub_expiry_code": "X"})
                else:
                    sub.sub_expiry_code = False
            else:
                sub.sub_expiry_code = False
                _logger.info("Expiration Codes Updated/Set for record: %s" % self.display_name)

    sub_expiry_code = fields.Selection([
        ("P", "Past Due"),
        ("R", "At Risk"),
        ("X", "Dead Sub")
    ], string="Expiration Code", store=True)

    order_type = fields.Selection([["Seller", "Seller"], ["Buyer", "Buyer"], ["Owner", "Owner"]], string="Order Type",
                                  compute="_get_order_type", store=True)
    
    

    last_payment_date = fields.Date("Last Payment Date", compute='_get_last_payment', store=True)

    estimated_sub_start_date = fields.Date("Est. Subscription Start Date", compute="_get_sub_days", store=False)
    estimated_sub_end_date = fields.Date("Est. Subscription End Date", compute="_get_sub_days", store=False)
    
    

    trade_call_fee = fields.Float(string='Trade Call Fee', compute="_get_trade_call_fee", store=False)
    user_id = fields.Many2one('res.users', string='Salesperson', tracking=True,  default=lambda self: self.env.user,
                              domain=lambda self: self._get_salesperson_domain())
    
    @api.depends('order_type')
    def _get_sub_days(self):
        for sub in self:
            """if sub.home_warranty.state == 'Buyer' and sub.home_warranty.estimated_closing_date:
                sub.estimated_sub_start_date = sub.home_warranty.estimated_closing_date
                sub.estimated_sub_end_date = (fields.Datetime.from_string(sub.home_warranty.estimated_closing_date) +
                                             relativedelta(months=int(sub.home_warranty.covered_buyer_term)) -
                                             relativedelta(days=1)).strftime('%Y-%m-%d')
            else:"""
            sub.estimated_sub_start_date = False
            sub.estimated_sub_end_date = False

    @api.depends('recurring_invoice_line_ids')
    def _get_order_type(self):
        for sub in self:
            t = False
            for product in sub.recurring_invoice_line_ids.mapped('product_id'):
                for attr in product.attribute_line_ids.mapped('value_ids'):
                    if attr.attribute_id.name == 'Target Consumer':
                        if attr.name == 'Buyer':
                            t = 'Buyer'
                        elif attr.name == 'Seller':
                            t = 'Seller'
                        elif attr.name == 'Homeowner':
                            t = 'Owner'
                        else:
                            print(sub.display_name + '-' + attr.name)
            sub.order_type = t

    @api.depends('recurring_invoice_line_ids')
    def _get_trade_call_fee(self):
        for sub in self:
            t = False
            for product in sub.recurring_invoice_line_ids.mapped('product_id'):
                for attr in product.attribute_line_ids.mapped('value_ids'):
                    if attr.attribute_id.name == 'Terms' and attr.trade_call_fee:
                        sub.trade_call_fee = attr.trade_call_fee

    @api.depends('recurring_invoice_line_ids')
    def _get_last_payment(self):
        for sub in self:
            lines = self.env['account.move.line'].search([['subscription_id', '=', sub.id]])
            date_last_paid = False
            for invoice in lines.mapped('move_id'):
                widget = json.loads(invoice['invoice_payments_widget'])
                if widget:
                    id = widget['content'][0]['account_payment_id']
                    last_payment_date_i = self.env['account.payment'].search([['id', '=', id]])['date'] # last payment date of invoice[i]
                    if not date_last_paid or date_last_paid < last_payment_date_i: date_last_paid = last_payment_date_i
            sub.last_payment_date = date_last_paid

    def get_sub_term_template(self, term):
        for sub in self:
            hw_term = term
            _logger.info(f' Current Term on HW: {hw_term}')
            hw_term = hw_term + "mon" if hw_term != "NC" else hw_term
            sub_template_id = self.env['sale.subscription.template'].search([('code', 'ilike', hw_term)])
            _logger.info(f'Located Sub template: {sub_template_id.name}')
            return sub_template_id.id


    # include address in subscription name for lookup
    def name_get(self):
        res = []

        for sub in self:
            name = sub.partner_id.sudo().name or ''
            if self._context.get('show_address') or self._context.get('show_address_only'):
                addr = ''
                if sub.home_warranty:
                    hw = sub.home_warranty
                    addr = hw._display_address()
                else:
                    addr = sub.partner_id.sudo()._display_address(without_company=True)
                if self._context.get('show_address_only'):
                    name = addr
                else:
                    name = name + "\n" + addr
            if self._context.get('show_home_warranty') and sub.home_warranty:
                name = name + "\n" + sub.home_warranty.name
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            name = '%s - %s' % (sub.code, name) if sub.code else name
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            elif self._context.get('inline'):
                name = name.replace('\n', ' - ')
            res.append(
                (sub.id, '%s/%s' % (sub.template_id.sudo().code, name) if sub.template_id.sudo().code else name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = ['|', ('code', operator, name), ('name', operator, name)]
        partners = self.env['res.partner'].search(['|', ('name', operator, name), ('street', operator, name)],
                                                  limit=limit)
        hw = self.env['home.warranty'].search(['|', ('name', operator, name), ('property_street', operator, name)],
                                              limit=limit)
        if partners or hw:
            domain = ['|', ('code', operator, name), '|',
                      ('name', operator, name), '|', ('partner_id', 'in', partners.ids),
                      ('home_warranty', 'in', hw.ids)]
        rec = self.search(domain + args, limit=limit)
        if self._context.get('show_address'):
            return rec.with_context({'show_address': '1', 'inline': '1', 'show_home_warranty': '1'}).name_get()
        else:
            return rec.name_get()

    home_warranty = fields.Many2one("home.warranty", "Home Warranty")
    realtor_contact = fields.Many2one("res.partner", string="Realtor", related="home_warranty.realtor_contact",
                                      store=True)
    closing_contact = fields.Many2one("res.partner", string="Closing Agent", related="home_warranty.closing_contact",
                                      store=True)

    property_street = fields.Char("Covered Street",related="home_warranty.property_street",
                                  tracking=True)

    # Street2
    property_street2 = fields.Char("Covered Street2", related="home_warranty.property_street2",
                                   tracking=True)

    # City
    property_city = fields.Char("Covered City", related="home_warranty.property_city",
                                tracking=True)

    # Zip
    property_zip = fields.Char("Covered Zip", related="home_warranty.property_zip",
                               tracking=True)

    # State
    property_state = fields.Many2one("res.country.state", string="Covered State", ondelete="restrict",
                                     related="home_warranty.property_state")

    # Customer State
    state = fields.Char(related='partner_id.state_id.code', string="Customer State")

    # Property Type
    property_type = fields.Selection(string="Property Type", related="home_warranty.property_type",
                                     tracking=True, store=True)

    submitter = fields.Many2one("res.users", string="Submitter", ondelete="restrict",
                                tracking=True)

    # @api.model
    # def _cron_recurring_create_invoice(self):
    #     future_date = (time+relativedelta(days=60)).strftime('%Y-%m-%d')
    #     domain = [('recurring_next_date', '<=', future_date),
    #               ('state', 'in', ['open', 'pending']),
    #               ('home_warranty','!=',False)]
    #     subscriptions = self.search(domain)
    #     for sub in subscriptions:
    #        sub.recurring_next_date = False

    def _get_subscription_end_date(self, cancel = False):
        """
            This method will return The Subscription End Date, which is calculated based On
            Subscription Template Duration.  Buyer orders have the end date set, but owner orders do not.
            cancel variable to track whether this function was triggered by a cancellation request
            :return: end_date -> datetime.date object
        """
        if (not self.home_warranty.covered_buyer_term) or (not self.date_start):
            return False

        today = datetime.today().date()
        if self.order_type == "Owner":
            end_date = self.recurring_next_date if self.recurring_next_date else self.date_start
        else:    
            end_date = self.home_warranty.estimated_closing_date
        # end_date = self.date_start if self.date_start != today else self.home_warranty.estimated_closing_date
        end_date = end_date if end_date else today
        if not cancel:
            interval_unit = {'daily': 'days',
                            'weekly': 'weeks',
                            'monthly': 'months',
                            'yearly': 'years'}
            recurring_unit = interval_unit[self.template_id.recurring_rule_type]
            recurring_interval = self.template_id.recurring_interval
            # Ensure that recurring_next_date will be in the future if this wasn't a cancellation
            recurring_next = end_date
            while recurring_next <= today:
                recurring_next += relativedelta(**{recurring_unit: recurring_interval})
            if recurring_next >= today:
                self['recurring_next_date'] = recurring_next
        elif cancel == 'cancel':
            self['recurring_next_date'] = False
        covered_term_id = self.home_warranty.get_covered_term_id()
        end_date += relativedelta(months=int(covered_term_id), days=-1)

        # If the subscription already has an end date that is later than what is calculated, assume it was updated manually and leave it alone
        if self.date and self.date > end_date:
            end_date = self.date        
        # Only set the end date if it's a buyer order, owner orders renew continually until cancelled.
        if self.order_type == "Buyer":
            self['date'] = end_date
        
        # MAKE SURE THIS CALCS RECURRING NEXT DATE (ONLY FOR BUYER ORDERS)
        # ADD FLOW FOR ALL SUB ORDER TYPES, TAKE LOGIC OUT OF GET_SUBS ON INVOICES

        # while covered_term_id:
        #     if end_date >= today:
        #         break
        #     end_date += relativedelta(months=1)
        #     covered_term_id -= 1
        return end_date

    def copy(self, default=None):
        """
            @Usage: Puted the restrictions, only those users are able to duplicate the home warranty
            whose are available in the 'Administration / Settings' group
            Ticket: [AO-798]
        """
        if self.env.user.has_group('base.group_system'):
            default = default or {}
            res = super(SaleSubscription, self).copy(default)
            return res
        raise UserError(_("You haven't access right to duplicate the subscription! Please contact your administrator."))

    def _prepare_invoice_data(self):
        res = super(SaleSubscription, self)._prepare_invoice_data()
        if res is None:
            res = {}
        res['home_warranty'] = self.home_warranty.id if self.home_warranty else False
        return res

class SaleSubscriptionLine(models.Model):
    _inherit = "sale.subscription.line"

    covered_items = fields.One2many("sale.subscription.line.coverage", "sale_subscription_line", "Covered Items")

    max_coverage = fields.Float("Max Coverage", related="product_id.standard_price")

    coverage_used = fields.Float("Amount Used", compute="_get_used_amount")

    @api.depends('product_id')
    def _get_used_amount(self):
        for r in self:
            claims = self.env["claims"].search([('product', '=', r.id)])
            amt = 0
            for c in claims:
                if c.paid_amt:
                    amt += c.paid_amt
                else:
                    amt += c.approved_amt
            r.coverage_used = amt

    def calc_coverage(self):
        if self.covered_items:
            return "Coverage calculation exists, please clear existing calculation"
        msg = ''
        items = self.env['product.product'].search(
            [('can_be_expensed', '=', True), ('warranty_terms_id.id', '=', self.product_id.warranty_terms_id.id)])
        for i in items:
            msg += '\t' + i.name.ljust(40) + ' ' + str(i.standard_price).rjust(10) + '\n'
            self.env['sale.subscription.line.coverage'].create(
                {'sale_subscription_line': self.id, 'product_id': i.id, })
        return msg


class SaleSubscriptionLineCoverage(models.Model):
    _name = "sale.subscription.line.coverage"
    _description = "Computed coverage for this subscription product with amount used"

    sale_subscription_line = fields.Many2one("sale.subscription.line", "Subscription Line")

    product_id = fields.Many2one('product.product', string='Product', required=True)

    name = fields.Char("Product Name", related="product_id.name")

    coverage = fields.Float("Max Coverage", related="product_id.standard_price")

    used_amt = fields.Float("Amount Used", compute="_get_used_amount")

    @api.depends('sale_subscription_line', 'product_id')
    def _get_used_amount(self):
        for r in self:
            claims = self.env["claim.items"].search([('subscription_line', '=', r.sale_subscription_line.id),
                                                     ('product_id', '=', r.product_id.id)])
            if r.product_id.id == 500:
                print(r.product_id.name)
            amt = 0
            for c in claims:
                amt += c.repair_amt
                print(str(amt))
            r.used_amt = amt
