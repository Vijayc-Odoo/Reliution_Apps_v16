# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime
import logging, re
from odoo.exceptions import UserError


_logger = logging.getLogger("##### Achosa #####")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_salesperson_domain(self):
        team_id = self.env.ref('sales_team.team_sales_department', raise_if_not_found=False)
        # return [('groups_id', 'in', self.env.ref('base.group_user').id),
        #         ('sale_team_id', '=', team_id.id if team_id else False)]
        return [('sale_team_id', '=', team_id.id if team_id else False)]

    @api.depends('realtor')
    def _get_realor_company(self):
        for rec in self:
            realtor_company = False
            if rec.realtor.parent_id:
                realtor_company = rec.realtor.parent_id.id #and rec.realtor.parent_id.id or rec.realtor.id
            rec.realtor_company = realtor_company

    home_warranty = fields.Many2one("home.warranty", "Home Warranty")

    realtor = fields.Many2one("res.partner", string="Realtor", related="home_warranty.realtor_contact",
                              store=True)
    realtor_email = fields.Char("Realtor Email", related="home_warranty.realtor_email",
                                store=True)
    realtor_company = fields.Many2one('res.partner', 'Realtor Company', store=True,
                                      compute='_get_realor_company')

    submitter = fields.Many2one("res.users", string="Submitter", ondelete="restrict",
                                tracking=True)

    order_type = fields.Selection([["Seller", "Seller"], ["Buyer", "Buyer"], ["Owner", "Owner"]], string="Order Type")

    subscription_start_date = fields.Date("Subscription Start Date")

    days_until_subscription = fields.Integer("Days until Subscription Start Date", compute="_get_sub_days",
                                      store=True, index=True)

    subscriptions = fields.Many2many("sale.subscription", compute="_get_subs", store=True)

    estimated_sub_start_date = fields.Date("Est. Subscription Start Date", compute="_get_sub_days", 
                                           store=False, compute_sudo=True)
    estimated_sub_end_date = fields.Date("Est. Subscription End Date", compute="_get_sub_days", 
                                         store=False, compute_sudo=True)
    
    hw_property_street = fields.Char("Covered Street", related="home_warranty.property_street",
                                store=True)
        
    user_id = fields.Many2one(
        'res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user,
        domain=lambda self: self._get_salesperson_domain())
    #hw_property_state = fields.Many2one("res.country.state", "HW State", related="home_warranty.property_state", store=True)

    @api.model    
    def create(self, vals):
        if "user_id" in vals:
            target_user = self.env["res.users"].browse(vals["user_id"])
            sale_team = target_user.sale_team_id
            if not target_user.sale_team_id or sale_team != self.env.ref("sales_team.team_sales_department"):
                #set to online sales user
                vals["user_id"] = self.env.ref("base.user_admin").id 
        res = super(SaleOrder, self).create(vals)
        return res


    @api.depends('order_line')
    def _get_subs(self):
        for o in self:
            subs = []
            lines = o.order_line
            for l in lines:
                if l.subscription_id and not l.subscription_id.id in subs:
                    subs.append(l.subscription_id.id)
            o.subscriptions = subs

    @api.depends('subscription_start_date')
    def _get_sub_days(self):
        for so in self:
            if so.subscription_start_date:
                so.days_until_subscription = (so.subscription_start_date - datetime.now().date()).days
            else:
                so.days_until_subscription = False
            if isinstance(so.home_warranty.covered_buyer_term,
                          str) and so.home_warranty.covered_buyer_term.isdigit() and so.order_type == 'Buyer' and so.invoice_status != 'invoiced' and so.home_warranty.estimated_closing_date:
                so.estimated_sub_start_date = so.home_warranty.estimated_closing_date
                so.estimated_sub_end_date = (so.home_warranty.estimated_closing_date +
                                             relativedelta(months=int(so.home_warranty.covered_buyer_term)) -
                                             relativedelta(days=1)).strftime('%Y-%m-%d')
            else:
                so.estimated_sub_start_date = False
                so.estimated_sub_end_date = False

    def action_mark_as_paid(self):
        super(SaleOrder, self).action_mark_as_paid()
        if self.home_warranty:
            self.home_warranty._get_invoiced()
        _logger.log(logging.INFO, "Sale Order paid: %s" % self.name)
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.home_warranty:
            self.home_warranty._get_invoiced()
        _logger.log(logging.INFO, "Sale Order confirmed: %s" % self.name)
        return res
    
    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent'])
        return orders.write({
            'state': 'draft',
            'signature': False,
            'signed_by': False,
            'signed_on': False,
        })
    
    def write(self, vals):
        """
        On record partner_id update: update home warranty
        :param vals:
        :return: bool - updated
        """
        res = super(SaleOrder, self).write(vals)
        if "partner_id" in vals and self.home_warranty:
            self.home_warranty._get_invoiced()
        return res
    
    def create_subscriptions(self):

        for o in self:
            # call default create
            subs = super(SaleOrder, o).create_subscriptions()
            order = o.sudo()
            subscriptions = self.env['sale.subscription'].sudo().browse(subs)
            
            #If salesperson field is not set, set it to home_warranty submitter field
            if o.home_warranty.submitter and not o.user_id:
                o.user_id = o.home_warranty.submitter
                
            # update fields on subscriptions
            for sub in subscriptions:
                lines = o.order_line
                
                values = {
                    'partner_id': o.partner_invoice_id.id,
                    'user_id': o.user_id.id,
                    'team_id': o.team_id.id}                
                value = list()
                for line in lines:
                    
                    alreadyExists = False
                    for product in sub.recurring_invoice_line_ids.mapped('product_id'):
                        if line.product_id.id == product.id:
                            alreadyExists = True
                    
                    if alreadyExists == False:
                        value.append((0, False, {
                            'product_id': line.product_id.id,
                            'name': line.name,
                            'quantity': line.product_uom_qty,
                            'uom_id': line.product_uom.id,
                            'price_unit': line.price_unit,
                            'discount': line.discount if line.order_id.subscription_management != 'upsell' else False,
                        })) 
    
                values['recurring_invoice_line_ids'] = value
                sub.write(values)
                
                sub.order_type = order.order_type
                sub.home_warranty = order.home_warranty
                if order.subscription_start_date:
                    start = order.subscription_start_date
                    sub.date_start = start
                    if sub.template_id:
                        next_date = start + relativedelta(months=1)
                        if sub.template_id.recurring_rule_type == "monthly":
                            next_date = start + relativedelta(months=sub.template_id.recurring_interval)
                        elif sub.template_id.recurring_rule_type == "daily":
                            next_date = start + relativedelta(days=sub.template_id.recurring_interval)
                        sub.recurring_next_date = next_date
                        if order.order_type == "Owner":
                            sub.date = False
                        else:
                            sub.date = next_date

    def _find_invoice_mail_template(self, template_id=False):
        
        if not template_id:
            prod_temp = self.order_line.filtered(lambda line: line.product_id.paid_email_template_id)[0].product_id.paid_email_template_id.id
            template_id = prod_temp if prod_temp else self.env.ref('account.email_template_edi_invoice').id

        return template_id


    def action_invoice_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        template_id = self._find_invoice_mail_template()
        # lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        # if template.lang:
        # lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'active_model': 'account.move',
            'active_ids': [self.invoice_ids[0].id],
            'active_id': self.invoice_ids[0].id,
            'default_model': 'account.move',
            'default_res_id': self.invoice_ids[0].id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            # 'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            # 'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            # 'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def _find_mail_template(self, force_confirmation_template=False):
        template_id = False
        if force_confirmation_template or (self.state == 'sale' and not self.env.context.get('proforma', False)):
            # template_id = self._find_invoice_mail_template() if self._find_invoice_mail_template() else int(self.env['ir.config_parameter'].sudo().get_param('sale.default_confirmation_template'))
            template_id = int(self.env['ir.config_parameter'].sudo().get_param('sale.default_confirmation_template'))
            template_id = self.env['mail.template'].search([('id', '=', template_id)]).id
            if not template_id:
                template_id = self.env['ir.model.data']._xmlid_to_res_id('sale.mail_template_sale_confirmation', raise_if_not_found=False)
            if template_id and self.mapped('home_warranty') and not self.mapped('order_type').__contains__('Owner'):
                _logger.info(f"Home Warranty: [{self.mapped('home_warranty.name')}], Order Type: [{self.mapped('order_type')}]")
                return False
        
        elif not template_id:
            template_id = self.env['ir.model.data']._xmlid_to_res_id('sale.email_template_edi_sale', raise_if_not_found=False)

        _logger.info(f"Sale Order Email Template Returned Id: [{template_id}]")
        return template_id


    def copy(self, default=None):
        """
            @Usage: Puted the restrictions, only those users are able to duplicate the home warranty
            whose are available in the 'Administration / Settings' group
            Ticket: [AO-798]
        """
        if self.env.user.has_group('base.group_system'):
            default = default or {}
            res = super(SaleOrder, self).copy(default)
            return res
        raise UserError(_("You haven't access right to duplicate the order! Please contact your administrator."))

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    @api.depends('product_id')
    def _get_related_program(self):
        for rec in self:
            program = self.sudo().env['coupon.program'].search([('discount_line_product_id', '=', rec.product_id.id)])
            rec.related_program = program

    related_program = fields.One2many('coupon.program', 'discount_line_product_id',
                                      compute="_get_related_program", store=False)

    def _prepare_invoice_line(self, **optional_values):
        """
        Override to add subscription-specific behaviours.
        Display the invoicing period in the invoice line description, link the invoice line to the
        correct subscription and to the subscription's analytic account if present, add revenue dates.
        """
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)  # <-- ensure_one()
        if self.subscription_id:
            res.update(subscription_id=self.subscription_id.id)
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            next_date = self.subscription_id.recurring_next_date or fields.Date.context_today(self)
            previous_date = next_date - relativedelta(**{periods[self.subscription_id.recurring_rule_type]: self.subscription_id.recurring_interval})
            is_already_period_msg = False
            if self.order_id.subscription_management != 'upsell':  # renewal or creation: one entire period
                date_start = previous_date
                date_start_display = previous_date
                date_end = next_date - relativedelta(days=1)  # the period does not include the next renewal date
            else:  # upsell: pro-rated period
                date_start, date_start_display, date_end = None, None, None
                try:
                    regexp = r"\[(\d{4}-\d{2}-\d{2}) -> (\d{4}-\d{2}-\d{2})\]"
                    match = re.search(regexp, self.name)
                    if match is not None and match:
                        date_start = fields.Date.from_string(match.group(1))
                        date_start_display = date_start
                        date_end = fields.Date.from_string(match.group(2))
                except Exception:
                    _logger.error('_prepare_invoice_line: unable to compute invoicing period for %r - "%s"', self, self.name)
                    # Fallback on discount
                if not date_start or not date_start_display or not date_end:
                    # here we have a slight problem: the date used to compute the pro-rated discount
                    # (that is, the date_from in the upsell wizard) is not stored on the line,
                    # preventing an exact computation of start and end revenue dates
                    # witness me as I try to retroengineer the ~correct dates 🙆‍
                    # (based on `partial_recurring_invoice_ratio` from the sale.subscription model)
                    total_days = (next_date - previous_date).days
                    days = round((1 - self.discount / 100.0) * total_days)
                    date_start = next_date - relativedelta(days=days+1)
                    date_start_display = next_date - relativedelta(days=days)
                    date_end = next_date - relativedelta(days=1)
                else:
                    is_already_period_msg = True
            if not is_already_period_msg:
                lang = self.order_id.partner_invoice_id.lang
                format_date = self.env['ir.qweb.field.date'].with_context(lang=lang).value_to_html
                # Ugly workaround to display the description in the correct language
                if lang:
                    self = self.with_context(lang=lang)
                _logger.log(logging.ERROR, res['name'])
                res.update({
                    'name': "".join(str(res['name']).split("Invoicing period")[0]) + '\n',
                })
            res.update({
                'subscription_start_date': date_start,
                'subscription_end_date': date_end,
            })
            if self.subscription_id.analytic_account_id:
                res['analytic_account_id'] = self.subscription_id.analytic_account_id.id
        return res
