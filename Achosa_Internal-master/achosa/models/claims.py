import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime
import datetime

_logger = logging.getLogger("##### Achosa #####")


class claims(models.Model):
    _name = 'claims'
    _description = 'claims'
    _inherit = ['mail.thread']
    _inherits = {}
    _order = 'id'

    # unique sequence number
    name = fields.Char("Claim Number",
                       readonly=True, default='New')

    # count of linked calls
    # TODO: action  to view and log calls - ON HOLD
    call_count = fields.Integer("Calls")

    # status of claim
    status = fields.Selection([('Init', 'Initiated'), ('Diag', 'Diagnosis Complete'),
                               ('Auth', 'Amount Authorized'), ('Comp', 'Complete'), ('Unlocked', 'Unlocked')]
                              , string="Status")

    # description of claim
    claim_desc = fields.Html("Description")

    # region subscription fields
    # Linked subscription
    subscription = fields.Many2one("sale.subscription", string="Subscription", ondelete="restrict")

    # Subscription Realtor
    subscription_realtor = fields.Char("Realtor", related="subscription.realtor_contact.name", store=True)

    # Subscription Status
    subscription_stage = fields.Selection("Subscription Status", related="subscription.stage_category", store=True)

    # Subscription Realtor's Company
    subscription_realtor_company = fields.Char("Realtor's Company",
                                               related="subscription.realtor_contact.commercial_company_name",
                                               store=True)

    # Subscription Last Payment Date
    last_payment_date = fields.Date("Subscription Last Payment Date", related="subscription.last_payment_date")

    # Subscription Start Date
    subscription_start = fields.Date("Subscription Start Date", related="subscription.date_start", store="False")

    # Subscription End Date
    subscription_end = fields.Date("Subscription End Date", related="subscription.date", store="False")

    # Linked subscription product
    product = fields.Many2one("sale.subscription.line", string="Product", ondelete="restrict")

    # Product Terms ID
    warranty_terms_id = fields.Many2many("product.attribute.value", compute="_compute_get_terms", store=False)

    # Coverage Description from product
    coverage_desc = fields.Html("Coverage",
                                related="product.product_id.description", store="True")

    # Checkbox for Conserve Claim
    conserve = fields.Boolean("Conserve", default=False)

    # Checkbox for Goodwill Claim
    goodwill = fields.Boolean("Goodwill", default=False)

    goodwill_amount = fields.Float("Goodwill Amount")

    goodwill_reason = fields.Text("Goodwill Reason")

    nipwo = fields.Selection([
        ('first30days', 'Less than 30 Days'),
        ('post30days', 'More than 30 Days'),
    ], string='NIPWO')

    estimated_sub_start_date = fields.Date("Est. Subscription Start Date", compute="_get_sub_days", store=False)
    estimated_sub_end_date = fields.Date("Est. Subscription End Date", compute="_get_sub_days", store=False)

    trade_call_fee = fields.Float(string='Trade Call Fee', compute="_get_trade_call_fee", store=True)

    claim_not_covered = fields.Boolean('Claim not covered')

    type_not_covered = fields.Selection([
        ('init', 'Initial Call'),
        ('diagnostic', 'Diagnostic Call')
    ], string='Not Covered Identified')

    reason_not_covered_init = fields.Selection([
        ('out_from_main_fundation', 'Outside the Main Foundation'),
        ('product_not_add', 'Item Specifically Not Included'),
        ('not_work', 'Not In Proper Working Order'),
        ('warranty_not_paid', 'Warranty never paid for'),
        ('not_scope', 'No Home Inspection'),
        ('cap_finished', 'Cap Reached'),

    ], string='Reason for init call')

    reason_not_covered_diagnostic = fields.Selection([
        ('out_from_main_fundation', 'Outside the Main Foundation'),
        ('product_not_add', 'Item Specifically Not Included'),
        ('not_work', 'Not In Proper Working Order'),
        ('non_normal_wear', 'Not Normal Wear and Tear'),
        ('work_without_approval', 'Work performed without approval'),
        ('without_maintenance', 'Lack Of Maintenance'),
        ('incorrect_installation', 'Improper Installation'),
        ('secondary_data', 'Secondary/Consequential damage'),

    ], string='Reason for diagnostic call')

    reason_not_covered = fields.Selection([
        ('out_from_main_fundation', 'Outside the Main Foundation'),
        ('product_not_add', 'Item Specifically Not Included'),
        ('not_work', 'Not In Proper Working Order'),
        ('warranty_not_paid', 'Warranty never paid for'),
        ('not_scope', 'No Home Inspection'),
        ('cap_finished', 'Cap Reached'),

        ('non_normal_wear', 'Not Normal Wear and Tear'),
        ('work_without_approval', 'Work performed without approval'),
        ('without_maintenance', 'Lack Of Maintenance'),
        ('incorrect_installation', 'Improper Installation'),
        ('secondary_data', 'Secondary/Consequential damage'),

    ], string='Not Covered Reason', compute="_get_reason_value")

    survey_sent = fields.Boolean("Customer Survey Sent", default=False)

    @api.depends('reason_not_covered_diagnostic', 'reason_not_covered_init', 'type_not_covered', 'claim_not_covered')
    def _get_reason_value(self):
        for claim in self:
            if not (claim.claim_not_covered or claim.type_not_covered):
                claim.type_not_covered = None
                claim.reason_not_covered = claim.reason_not_covered_diagnostic
            else:
                if claim.type_not_covered == 'init':
                    claim.reason_not_covered = claim.reason_not_covered_init
                elif claim.type_not_covered == 'diagnostic':
                    claim.reason_not_covered = claim.reason_not_covered_diagnostic
                else:
                    claim.reason_not_covered = None

    @api.onchange('claim_not_covered')
    def _onchange_claim_not_covered(self):
        if not self.claim_not_covered:
            self.type_not_covered = None

    @api.onchange('type_not_covered')
    def _onchange_type_not_covered(self):
        self.reason_not_covered_diagnostic = None
        self.reason_not_covered_init = None

    @api.depends('subscription')
    def _get_trade_call_fee(self):
        for cl in self:
            cl.trade_call_fee = 0
            try:
                sub = cl.subscription
                for product in sub.recurring_invoice_line_ids.product_id:
                    for attr in product.attribute_line_ids.product_template_value_ids.product_attribute_value_id:
                        if attr.attribute_id.name == 'Terms' and attr.trade_call_fee > 0:
                            cl.trade_call_fee = attr.trade_call_fee
            except:
                return

    @api.depends('subscription')
    def _get_sub_days(self):
        for cl in self:
            sub = cl.subscription
            if isinstance(sub.home_warranty.covered_buyer_term,
                          str) and sub.home_warranty.covered_buyer_term.isdigit() and sub.home_warranty.state == 'Buyer' and sub.home_warranty.estimated_closing_date:
                cl.estimated_sub_start_date = sub.home_warranty.estimated_closing_date
                cl.estimated_sub_end_date = (fields.Datetime.from_string(sub.home_warranty.estimated_closing_date) +
                                             relativedelta(months=int(sub.home_warranty.covered_buyer_term)) -
                                             relativedelta(days=1)).strftime('%Y-%m-%d')
            else:
                cl.estimated_sub_start_date = cl.subscription_start
                cl.estimated_sub_end_date = cl.subscription_end

    @api.depends('subscription', 'product', 'items')
    def _compute_get_terms(self):
        for c in self:
            c.terms = False
            c.item_terms = False
            c.warranty_terms_id = False
            try:
                c.terms = c.product.product_id.warranty_terms
                c.warranty_terms_id = c.product.product_id.warranty_terms_id
                if c.items:
                    if c.items[0].product_id.warranty_terms_id == c.warranty_terms_id:
                        c.item_terms = c.items[0].product_id.terms_short
            except:
                c.terms = "Error loading"

    # Coverage Terms from product
    terms = fields.Html("Terms", compute="_compute_get_terms")
    item_terms = fields.Html("Item Terms", compute="_compute_get_terms")

    @api.onchange('subscription')
    def change_subscription(self):
        if self.subscription:
            p = self.env['sale.subscription.line'].search([['analytic_account_id', '=', self.subscription.id]])
            if len(p) > 0:
                self.product = p.ids[0]
                self.terms = self.product.product_id.warranty_terms
                self.warranty_terms_id = self.product.product_id.warranty_terms_id

    # endregion

    # region Customer Fields
    # Linked Customer - from subscription
    customer = fields.Many2one("res.partner", string="Customer", ondelete="restrict",
                               related="subscription.partner_id", store="True")

    # customer email
    cust_email = fields.Char("Email",
                             related="subscription.partner_id.email", store="True")

    # customer phone
    cust_phone = fields.Char("Phone",
                             related="subscription.partner_id.phone", store="True")

    # property street
    property_street = fields.Char("Street",
                                  related="subscription.property_street", store="True")

    # property state
    property_state = fields.Many2one("res.country.state", string="Covered State", ondelete="restrict",
                                     related="subscription.property_state", store="True")

    # all claims by this customer
    cust_claims = fields.Integer(compute='_compute_cust_claims', string="Claims count")

    # claims
    claims = fields.One2many("claims", "customer", related="customer.claims")

    def _compute_cust_claims(self):
        for c in self:
            c.cust_claims = len(c.customer.claims)

    # endregion

    # region Technician / Diag Fields
    # Technician
    tech = fields.Many2one("res.partner", string="Technician", ondelete="restrict",
                           )

    # Technician email
    tech_email = fields.Char("Tech Email",
                             related="tech.email", store="True")

    # Technician phone
    tech_phone = fields.Char("Tech Phone",
                             related="tech.phone", store="True")

    # Tech Company
    company = fields.Many2one("res.partner", string="Company", ondelete="restrict",
                              related="tech.parent_id", store="True")

    # Diagnosis description
    diag_desc = fields.Html("Diagnosis Description")

    # endregion

    # region Amount Fields
    # Approved claim amount
    approved_amt = fields.Float("Amount Approved")

    # Date amount was approved
    approved_date = fields.Datetime("Date Approved")

    # Claim Amount Requested
    requested_amt = fields.Float("Amount Requested")

    # Date Amount was requested
    request_date = fields.Datetime("Date Requested")

    # Amount paid
    paid_amt = fields.Float("Amount Paid")

    # Date paid
    paid_date = fields.Datetime("Date Paid")

    # endregion

    @api.onchange('approved_amt')
    def onchange_approved_amt_warning(self):
        if not self.approved_amt:
            return

        warning = self._get_used_amount(self.approved_amt)
        if warning:
            return {'warning': warning}

    @api.onchange('requested_amt')
    def onchange_requested_amt_warning(self):
        if not self.requested_amt:
            return

        warning = self._get_used_amount(self.requested_amt)
        if warning:
            return {'warning': warning}

    @api.onchange('paid_amt')
    def onchange_paid_amt_warning(self):
        if not self.paid_amt:
            return

        warning = self._get_used_amount(self.paid_amt)
        if warning:
            return {'warning': warning}

    def _get_used_amount(self, new_amt):
        title = ("Warning Exceeds Max Coverage")
        claims = self.env["claims"].search([('product', '=', self.product.id), ('name', '!=', self.name)])
        amt = new_amt
        for c in claims:
            if c.paid_amt:
                amt += c.paid_amt
            else:
                amt += c.approved_amt
        if amt > self.product.max_coverage:
            message = ("Exceeds Max Coverage for: \n{0}\nMax Coverage {1}\nAmount Used: {2}").format(
                self.product.name,
                self.product.max_coverage,
                amt
            )
            return {
                'title': title,
                'message': message,
            }
        return False

    # region log times of status change

    # Date Diagnosed
    diag_date = fields.Datetime("Date Diagnosed")

    # Date Authorized
    auth_date = fields.Datetime("Date Authorized")

    # Date Completed
    comp_date = fields.Datetime("Date Completed")

    # endregion

    # region suggested vendors
    # Suggested Vendors for the claim
    suggested_vendors = fields.Many2many("res.partner", string="Suggested Vendors", ondelete="restrict",
                                         compute="_find_suggested_vendor", store=False)

    @api.model
    @api.depends('subscription')
    def _find_suggested_vendor(self):
        zip = self.env['vendor.zip.codes'].search([('zip_code', '=', self.subscription.home_warranty.property_zip)])
        vendors = False
        for z in zip:
            if vendors:
                vendors = vendors + self.env['res.partner'].search(
                    [('id', '=', z.vendor.id), ('vendor_type', '=', 'Tech')])
            else:
                vendors = self.env['res.partner'].search([('id', '=', z.vendor.id), ('vendor_type', '=', 'Tech')])
        self.suggested_vendors = vendors

    # endregion

    # region Item fields
    # Items repaired
    items = fields.One2many("claim.items", "claims_id", string="Claim Item Lines")

    def _compute_item_name(self):
        for c in self:
            if len(c.items) > 0:
                c.item_name = c.items[0].product_id.name
            else:
                c.item_name = "________"

    item_name = fields.Char("Item Name", compute="_compute_item_name", store=True)

    coverage_list = fields.One2many("sale.subscription.line.coverage", related="product.covered_items")

    user_id = fields.Many2one(comodel_name='res.users', string='Salesperson', related="subscription.user_id")

    @api.onchange('items')
    def _update_item_name(self):
        for c in self:
            if len(c.items) > 0:
                c.item_name = c.items[0].product_id.name
            else:
                c.item_name = "________"

    # endregion
    @api.model
    def check_condition_show_dialog(self, record_id, data_changed):
        '''
        :param:   self: current model
                  record_id: id of record if save on write function, False on create function
                  data_changed: data changed on form
        :returns: True: show dialog
                  False: ignore dialog
        '''
        return True

    @api.model
    def claim_subcription_exists(self, data):
        new_subscription_id = int(data['data']['subscription'])
        try:
            claim_id = int(data['data']['id'])
        except:
            claim_id = 0
        claims = self.env['claims'].search([('subscription', '=', new_subscription_id), ('status', '!=', 'Comp')])
        claim_data = {}

        if (len(claims) > 0):
            for c in claims:
                if c.status != 'Comp' and claim_id != c.id and c.item_name == data['data']['item_name']:
                    claim_data['name'] = c.name
                    claim_data['status'] = c.status
                    claim_data['id'] = c.id
        return claim_data

    @api.model
    def create(self, vals):
        '''
        Create the record - Set the name to next seq number
        :param vals: values to write to the new record
        :return: successful?
        '''
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'claim.number.seq') or '/'
            vals['status'] = 'Init'
        rec = super(claims, self).create(vals)
        if rec.tech:
            if not rec.tech.vendor_type:
                rec.tech.vendor_type = "Tech"
        if rec.product and not rec.product.covered_items:
            print(rec.name)
            print(rec.product.calc_coverage())
        return rec

    def write(self, values):
        '''
        on record update
        set dates when updating: amount requested, approved, and paid on save
        :param values: new values to write to the database
        :return: successful?
        '''
        res = super(claims, self).write(values)
        for rec in self:
            if rec.approved_amt > 0 and not rec.approved_date:
                rec.approved_date = datetime.datetime.now()
            if rec.requested_amt > 0 and not rec.request_date:
                rec.request_date = datetime.datetime.now()
            if rec.paid_amt > 0 and not rec.paid_date:
                rec.paid_date = datetime.datetime.now()
            if rec.tech:
                if not rec.tech.vendor_type:
                    rec.tech.vendor_type = "Tech"
                if not rec.tech.email:
                    rec.tech.email = rec.tech_email
                if not rec.tech.phone:
                    rec.tech.phone = rec.tech_phone
                if not rec.tech.parent_id and rec.company:
                    rec.tech.parent_id = rec.company
                    rec.tech.parent_id.company_type = "company"
                # rec.tech.supplier = True
                # didn't manage in v15
                # rec.tech.customer = False
            if rec.product and not rec.product.covered_items:
                print(rec.name)
                print(rec.product.calc_coverage())

        return res

    # region Status Actions
    # update status: Diagnosis Complete
    def action_diag(self):
        c = self.filtered(lambda s: s.status == 'Init')
        return c.write({
            'status': 'Diag',
            'diag_date': fields.Datetime.now(),
        })

    # update status: Claim Amount Authorized
    def action_auth(self):
        for claim in self:
            if claim.claim_not_covered and not claim.type_not_covered:
                raise ValidationError('Please select a value for Not Covered Identified before authorizing this claim')

            if claim.claim_not_covered and claim.type_not_covered and not claim.reason_not_covered:
                raise ValidationError(
                    'Please select a value for Not Covered Identified field before authorizing this claim')

        if not self.goodwill:
            c = self.filtered(lambda s: s.status == 'Diag')
            return c.write({
                'status': 'Auth',
                'auth_date': fields.Datetime.now(),
            })
        else:
            if self.goodwill and self.goodwill_amount > 0 and self.goodwill_reason:
                c = self.filtered(lambda s: s.status == 'Diag')
                return c.write({
                    'status': 'Auth',
                    'auth_date': fields.Datetime.now(),
                })
            else:
                raise UserError(("Type Goodwill amount and reason before authorizing this claim"))

    def action_complete_f(self):
        c = self.filtered(lambda s: s.status == 'Auth')
        exists = False
        # res = super(claims, self).create(vals)
        zips = self.env['vendor.zip.codes'].search(
            [('vendor', '=', self.tech.id), ('zip_code', '=', self.subscription.home_warranty.property_zip)])
        if zips:
            exists = True
        if exists == False:
            self.env['vendor.zip.codes'].create({
                'vendor': self.tech.id,
                'zip_code': self.subscription.home_warranty.property_zip,
            })
        return c.write({
            'status': 'Comp',
            'comp_date': fields.Datetime.now(),
        })

    # update status: Claim Complete
    @api.depends('subscription')
    def action_complete(self):
        for claim in self:
            if claim.claim_not_covered and not claim.type_not_covered:
                raise ValidationError('Please select a value for Not Covered Identified before completing this claim')

            if claim.claim_not_covered and claim.type_not_covered and not claim.reason_not_covered:
                raise ValidationError(
                    'Please select a value for Not Covered Identified field before completing this claim')

        if not self.goodwill:
            self.action_complete_f()
        else:
            if self.goodwill and self.goodwill_amount > 0 and self.goodwill_reason:
                self.action_complete_f()
            else:
                raise UserError(("Type Goodwill amount and reason before completing this claim"))

    # update status: Claim Unlock
    def action_unlock(self):
        c = self.filtered(lambda s: s.status == 'Comp')
        return c.write({
            'status': 'Unlocked',
        })

    # update status: Claim Lock - Complete
    def action_lock(self):
        c = self.filtered(lambda s: s.status == 'Unlocked')
        return c.write({
            'status': 'Comp',
        })

    # endregion

    # region Attachment Field and Action
    # count of attached files
    attachment_count = fields.Integer(compute='_compute_attachment_count', string="File")

    def _compute_attachment_count(self):
        attachment_data = self.env['ir.attachment'].read_group(
            [('res_model', '=', self._name), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        mapped_data = dict([(data['res_id'], data['res_id_count']) for data in attachment_data])
        for c in self:
            c.attachment_count = mapped_data.get(c.id, 0)

    def action_open_attachments(self):
        self.ensure_one()
        return {
            'name': _('Digital Attachments'),
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,form',
            'view_type': 'form',
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id),
            'help': """
                <p class="oe_view_nocontent_create">Click on create to add attachments for this Claim.</p>
                """,
        }

    # endregion

    # count of Emails Sent
    email_count = fields.Integer(compute='_compute_attachment_emails', string="Emails")

    def _compute_attachment_emails(self):
        mail_data = self.env['mail.mail'].read_group([('model', '=', self._name), ('res_id', 'in', self.ids)],
                                                     ['res_id'], ['res_id'])
        mapped_data = dict([(data['res_id'], data['res_id_count']) for data in mail_data])
        for c in self:
            c.email_count = mapped_data.get(c.id, 0)

    def _get_email_context(self):
        try:
            if self.status == 'Init':
                template_id = self.env['mail.template'].search([('name', '=', 'Claim Email Init (Option 1)')]).id
            else:
                template_id = self.env['mail.template'].search([('name', '=', 'Claim Email ' + self.status)]).id
            # template_id = self.env['mail.template'].search([('name', '=', 'Claim Email '+self.status)]).id
        except ValueError:
            template_id = False
        ctx = {
            'default_model': 'claims',
            'default_res_id': self.ids[0],
            'default_subject': 'Your claim %s' % str(self.name),
            'default_email_from': 'claims@achosahw.com',
            'default_reply_to': 'claims@achosahw.com',
            'default_recipient_ids': [self.customer.id],
            'default_partner_ids': [self.customer.id],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_auto_delete': False,
            'mark_so_as_sent': True,
            'force_email': True
        }
        return ctx

    def action_open_emails(self):
        self.ensure_one()
        ctx = self._get_email_context()
        return {
            'name': _('Emails'),
            'domain': [('model', '=', self._name), ('res_id', '=', self.id)],
            'res_model': 'mail.mail',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,form',
            'view_type': 'form',
            'context': str(ctx),
            'help': """
                <p class="oe_view_nocontent_create">Click on create to send an email for this Claim.</p>
                """,
        }

    # TODO: allow attachment of terms
    def action_send_email(self):
        '''
        This function opens a window to compose an email, with the edi claim template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']

        ctx = self._get_email_context()
        # try:
        #    compose_form_id = ir_model_data.get_object_reference('achosa', 'email_compose_claims')[1]
        # except ValueError:
        #    compose_form_id = False
        compose_form_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def copy(self, default=None):
        """
            @Usage: Puted the restrictions, only those users are able to duplicate the home warranty
            whose are available in the 'Administration / Settings' group
            Ticket: [AO-798]
        """
        if self.env.user.has_group('base.group_system'):
            default = default or {}
            res = super(claims, self).copy(default)
            return res
        raise UserError(_("You haven't access right to duplicate the claim! Please contact your administrator."))
