import logging
from odoo import api, fields, tools, models

_LOGGER = logging.getLogger("##### Achosa #####")


class Lead(models.Model):
    _inherit = 'crm.lead'

    def _get_salesperson_domain(self):
        team_id = self.env.ref('sales_team.team_sales_department', raise_if_not_found=False)
        # return [('groups_id', 'in', self.env.ref('base.group_user').id),
        #         ('sale_team_id', '=', team_id.id if team_id else False)]
        return [('sale_team_id', '=', team_id.id if team_id else False)]

    partner_company = fields.Many2one('res.partner', string='Linked Company', tracking=True,  index=True,
                                      help="Linked company (optional). Will not be auto created.")
    parent_id = fields.Many2one('res.partner', string="Office", related="partner_id.parent_id", readonly=False)
    total_orders = fields.Integer("Total Home Warranties Entered", compute="_get_count_hw", store=True, index=True)
    opt_email = fields.Boolean('Opt-in Emails', store=True)
    dup = fields.Many2one("res.partner", string="Duplicate Emails", ondelete="restrict",
                          help="List of Existing contacts with this email address")

    contact_link_phone = fields.Char("Contact Phone")
    contact_link_email = fields.Char("Contact Email")
    contact_link_mobile = fields.Char("Contact Mobile")
    contact_link_name = fields.Char("Name")
    contact_link_vendor_type = fields.Selection(
        [("Realtor", "Realtor"), ("Tech", "Technician"), ("Closing", "Closing Agent"),
         ("Coordinator", "Coordinator")], "Contact Vendor Type")

    # customer phone
    cust_phone = fields.Char("Customer Mobile",
                             related="partner_id.mobile", store="True")
    user_id = fields.Many2one('res.users', string='Salesperson', related="partner_id.user_id", index=True,
                              tracking=True,  readonly=False, default=lambda self: self.env.user,
                              domain=lambda self: self._get_salesperson_domain())

    @api.depends('partner_id', 'parent_id')
    def _compute_name(self):
        res = super(Lead, self)._compute_name()
        for lead in self:
            partner_id = lead.partner_id
            if partner_id and (partner_id.parent_id or lead.parent_id):
                name = partner_id.parent_id.name.strip() if partner_id.parent_id else lead.parent_id.name.strip()
                lead.name = f"{name} - {partner_id.name.strip()}"
            elif partner_id:
                lead.name = f"{partner_id.name.strip()}"
        return res

    @api.onchange('dup')
    def _dup_pick(self):
        if self.dup:
            self.partner_id = self.dup

    def _create_lead_partner(self):
        """ OVERRIDE - Do not create the company
            Create a partner from lead data
            :returns res.partner record
        """
        if self.partner_id:
            return self.partner_id

        Partner = self.env['res.partner']

        return Partner.create(
            self._create_lead_partner_data(self.contact_name if self.contact_name else self.name, False,
                                           self.partner_company.id if self.partner_company else False))

    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        """ extract data from lead to create a partner
            :param name : furtur name of the partner
            :param is_company : True if the partner is a company
            :param parent_id : id of the parent partner (False if no parent)
            :returns res.partner record
        """
        email_split = tools.email_split(self.email_from)
        return {
            'name': name,
            'user_id': self.env.context.get('default_user_id') or self.user_id.id,
            'comment': self.description,
            'team_id': self.team_id.id,
            'parent_id': parent_id,
            'phone': self.phone,
            'mobile': self.mobile,
            'email': email_split[0] if email_split else False,
            'title': self.title.id,
            'function': self.function,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'country_id': self.country_id.id,
            'state_id': self.state_id.id,
            'website': self.website,
            'is_company': is_company,
            'type': 'contact',
            'vendor_type': 'Realtor'
            # 'supplier': True
        }

    def _get_new_hw_context(self):
        ctx = {
            'default_realtor_contact': self.partner_id.id
        }
        return ctx

    def action_new_hw(self):
        '''
        This function opens a window to create home warranty
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']

        ctx = self._get_new_hw_context()
        try:
            compose_form_id = ir_model_data.check_object_reference('achosa', 'default_form_view_for_hw')[1]
        except ValueError:
            compose_form_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'home.warranty',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_sale_quotations_new(self):
        action = self.env["ir.actions.actions"]._for_xml_id("achosa.action_home_warranty_lead")
        action['context'] = {
            'default_property_street': self.street,
            'default_property_street2': self.street2,
            'default_property_city': self.city,
            'default_property_state': self.state_id.id,
            'default_property_zip': self.zip,
            'default_default_partner_id': self.partner_id.id,
        }
        # opportunity as per 13
        # all the view as per 13

        return action
        # home_warranty_obj = self.env['home.warranty'].create({
        # })
        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'form',
        #     'res_model': 'home.warranty',
        #     'target': 'current',
        #     'res_id': home_warranty_obj.id,
        #     'context': {'default_partner_id': self.partner_id.id},
        # }


    def _get_count_hw(self):
        for rec in self:
            hw = self.env['home.warranty'].search_read([('realtor_contact', '=', rec.partner_id.id)], ['create_date'])
            rec.total_orders = len(hw)

    def action_view_home_warranties(self):
        """
        Open Seller Order
        :return:
        """
        self.ensure_one()
        ctx = self._get_new_hw_context()
        return {
            'name': ('Home Warranties'),
            'domain': [('realtor_contact', '=', self.partner_id.id)],
            'res_model': 'home.warranty',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': ctx,
            'help': """
                        <p class="oe_view_nocontent_create">No Home Warranties for this Realtor.</p>
                        """,
        }

    def action_grant_portal_access(self):
        """
        Open Grant Portal Access
        :return:
        """
        self.ensure_one()
        ir_model_view = self.env['ir.ui.view']

        ctx = {
            'active_ids': self.partner_id.id
        }
        try:
            compose_form_id = ir_model_view.get_view_id('partner_wizard_action')
        except ValueError:
            compose_form_id = False
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'portal.wizard',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.onchange('contact_link_phone', 'contact_link_email', 'contact_link_mobile', 'contact_link_name',
                  'contact_link_vendor_type')
    def link_contact(self):
        if self.contact_link_phone not in ["", None, False]:
            self.partner_id.phone = self.contact_link_phone
        if self.contact_link_email not in ["", None, False]:
            self.partner_id.email = self.contact_link_email
        if self.contact_link_mobile not in ["", None, False]:
            self.partner_id.mobile = self.contact_link_mobile
        if self.contact_link_name not in ["", None, False]:
            self.partner_id.name = self.contact_link_name
        if self.contact_link_vendor_type not in ["", None, False]:
            self.partner_id.vendor_type = self.contact_link_vendor_type

    @api.onchange('partner_id', 'email_from', 'phone')
    def update_contact_fields(self):
        email_from = self.email_from if self.email_from else self.partner_id.email
        phone = self.phone if self.phone else self.partner_id.phone
        self.contact_link_phone = phone
        self.contact_link_email = email_from
        self.contact_link_mobile = self.partner_id.mobile
        self.contact_link_name = self.partner_id.name
        self.contact_link_vendor_type = self.partner_id.vendor_type
        # if self.partner_id.parent_id:
        #     # self.contact_link_company = self.partner_id.parent_id.name
        if self.partner_id.user_id.name not in ["", None, False] and self.user_id.name in ["", None, False,
                                                                                           self.env.user.name]:
            self.user_id = self.partner_id.user_id

    def get_hw_partner_lead_ids(self, partner_id):
        lead_action_dict = partner_id.action_view_opportunity()
        lead_ids = self.search(lead_action_dict['domain'])
        return lead_ids

    def create_hw_lead(self, home_warranty_id, realtor_partner_id, **kwargs):
        lead_id = self.create(self._prepare_hw_lead_values(realtor_partner_id, **kwargs))
        lead_id.convert_opportunity(partner_id=realtor_partner_id.id)
        lead_id.message_post(body=f"Auto generated from {home_warranty_id.name}")
        lead_id._update_hw_lead_status(realtor_partner_id)
        return lead_id

    def _prepare_hw_lead_values(self, partner_id, **kwargs):
        values = {
            'type': "lead",
            'name': partner_id.name or '',
            'partner_id': partner_id.id,
            'user_id': kwargs.get('user_id', False) or self.user_id.id,
            'team_id': self.env['crm.team'].search([('name', '=', 'Sales')], limit=1).id
        }
        _LOGGER.info(f"CRM Lead Values: [{values}]")
        return values

    def _update_hw_lead_status(self, partner_id):
        new_customer_stage_id = self.env.ref('crm.stage_lead4', raise_if_not_found=False)
        home_warranty_ids = self.env['home.warranty'].get_realtor_home_warranty_ids(partner_id)
        if len(home_warranty_ids) >= 4:
            self.action_set_won_rainbowman()
        else:
            self.write({'stage_id': new_customer_stage_id.id})
        return True

    # def update_hw_partner_lead_status(self, partner_id):
    #     """
    #         This method is update the status of lead
    #         :param order_id: sale.order()
    #         :return: Boolean
    #     """
    #     lead_ids = self.env['crm.lead'].get_hw_partner_lead_ids(partner_id)
    #     lead_id = lead_ids[0] if lead_ids else []
    #     if lead_id:
    #         stage_id = self.env.ref('crm.stage_lead4', raise_if_not_found=False)
    #         if stage_id:
    #             lead_id.stage_id = stage_id.id
    #     return True


class CrmTeam(models.Model):
    _inherit = "crm.team"

    member_ids = fields.One2many(
        'res.users', 'sale_team_id', string='Channel Members', check_company=True,
        help="Add members to automatically assign their documents to this sales team. You can only be member of one team.")
