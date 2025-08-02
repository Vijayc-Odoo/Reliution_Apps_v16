import logging
from odoo import api, fields, models, tools, _

_logger = logging.getLogger("##### Achosa #####")

class Product(models.Model):
    _inherit = "product.product"

    @api.depends('attribute_line_ids')
    # Get attribute ids for searching
    def _compute_get_terms(self):
        for p in self:
            # Get Terms Attribute ID
            p.warranty_terms = ''
            # p.warranty_terms_long = ''
            # if p.warranty_terms_id:
            #     t = p.warranty_terms_id
            #     p.warranty_terms = t.notes
            #     p.warranty_terms_long = t.description
            # else:
            p.warranty_terms_id = False
            for t in p.product_template_attribute_value_ids.product_attribute_value_id:
                if t.attribute_id.name == 'Terms':
                    p.warranty_terms_id = t
                    p.warranty_terms = t.notes
                    p.warranty_terms_long = t.description
            # Get Term Length Attribute ID
            # if p.warranty_term_id:
            #     t = p.warranty_term_id
            # else:
            p.warranty_term_id = False
            for t in p.product_template_attribute_value_ids.product_attribute_value_id:
                if t.attribute_id.name == 'Term':
                    p.warranty_term_id = t
            # Get Property Type Attribute ID
            # if p.warranty_property_id:
            #     t = p.warranty_property_id
            # else:
            p.warranty_property_id = False
            for t in p.product_template_attribute_value_ids.product_attribute_value_id:
                if t.attribute_id.name == 'Property Type':
                    p.warranty_property_id = t
            # Get Target Consumer Attribute ID
            # if p.warranty_consumer_id:
            #     t = p.warranty_consumer_id
            # else:
            p.warranty_consumer_id = False
            for t in p.product_template_attribute_value_ids.product_attribute_value_id:
                if t.attribute_id.name == 'Target Consumer':
                    p.warranty_consumer_id = t

    def _is_renewal(self):
        for p in self:
            renewal = False
            for t in p.product_template_attribute_value_ids.product_attribute_value_id:
                if t.attribute_id.name == 'Renewal Term':
                    renewal = True
            p.renewal = renewal

    # Renewal
    renewal = fields.Boolean("Renewal", compute="_is_renewal", store=True)

    # Term ID
    warranty_term_id = fields.Many2one("product.attribute.value", string="Term Length ID",
                                       compute="_compute_get_terms", store=True)

    # Property ID
    warranty_property_id = fields.Many2one("product.attribute.value", string="Property Type ID",
                                           compute="_compute_get_terms", store=True)

    # Property ID
    warranty_consumer_id = fields.Many2one("product.attribute.value", string="Target Consumer ID",
                                           compute="_compute_get_terms", store=True)

    # Terms ID
    warranty_terms_id = fields.Many2one("product.attribute.value", string="Terms ID",
                                        compute="_compute_get_terms", store=True)

    # terms of warranty
    warranty_terms = fields.Html("Terms", compute="_compute_get_terms",
                                 compute_sudo=True)

    # terms of warranty for print
    warranty_terms_long = fields.Html("Terms for print", compute="_compute_get_terms",
                                      compute_sudo=True)

    # shortened terms of warranty for item
    terms_short = fields.Html("Short Terms",
                              compute_sudo=True)

    renewal_product = fields.Many2one("product.product", "Default Renewal Variant")

    renewed_by = fields.One2many("product.product", "renewal_product", "Renewed By")

    def find_property_type_product(self, home_warranty_product_id):
        self.ensure_one()
        attribute_values_list = []
        for product_attribute_value_id in home_warranty_product_id.product_template_attribute_value_ids.product_attribute_value_id:
            attribute_name = product_attribute_value_id.attribute_id.name.lower() if product_attribute_value_id.attribute_id else ''
            if attribute_name in ['property type', 'term', 'renewal term']:
                attribute_values_list.append(product_attribute_value_id.id)

        for product_attribute_value_id in self.product_template_attribute_value_ids.product_attribute_value_id:
            if product_attribute_value_id.term_product_type and product_attribute_value_id.term_product_type.lower() == 'addon':
                attribute_values_list.append(product_attribute_value_id.id)
                break

        field = 'product_template_attribute_value_ids.product_attribute_value_id.id'
        domain = []
        for product_attribute_value_id in attribute_values_list:
            domain.append((field, 'in', [product_attribute_value_id]))

        product_id = self.search(domain, limit=1)
        if not product_id:
            product_id = self
        _logger.info(f"Domain : {domain}, Product : {product_id.ids}")
        return product_id


class ProductAttributeValue(models.Model):
    _inherit = ['mail.thread', "product.attribute.value"]
    _name = "product.attribute.value"

    trade_call_fee = fields.Float(string='Trade Call Fee')

    # Status
    state = fields.Selection([["Draft", "Draft"], ["Active", "Active hidden"],
                              ["Published", "Published on web"], ["Archived", "Archived hidden"]], string="Status",
                             default="Draft")

    # States for Terms
    states = fields.Many2many("res.country.state", "product_attribute_value_states", "value_id", "state_id"
                              , string="States", ondelete="restrict",
                              domain=[["enable_home_warranty", "=", True]])

    # Notes about attribute, used for Terms for the Terms attribute
    notes = fields.Html("Short Description")

    # type of term product
    term_product_type = fields.Selection(
        [["Seller", "Home Seller's Service"], ["Buyer", "Home Buyer's Service"],
         ["Owner", "Home Owner's Service"], ["AddOn", "Add On"]]
        , string="Term Product Type",
        tracking=True)

    # Printed Notes about attribute, used for Terms for the Terms attribute
    description = fields.Html("Long Description")

    attachment_ids = fields.One2many("ir.attachment", "res_id", "Attachments",
                                     domain=[('res_model', '=', 'product.attribute.value')])

    seller_seller_email_template = fields.Many2one("mail.template", "Seller Order to Seller")

    seller_realtor_email_template = fields.Many2one("mail.template", "Seller Order to Realtor")

    def action_archive(self):
        attachment_ids = []
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'product.attribute.value'),
            ('res_id', '=', self.id)])
        for attach in attachments:
            attachment_ids.append(attach.id)
        if len(attachment_ids) > 0:
            msg = self.env['mail.channel'].search([('name', '=', 'TERMS')]).message_post(
                body='Archived the following terms documents.',
                subject='Archive', message_type='comment',
                subtype='mail.mt_comment', attachment_ids=attachment_ids)
            msg.model = 'product.attribute.value'
            msg.res_id = self.id
            msg.record_name = self.display_name
            for attach in attachments:
                attach.model = 'mail.message'
                attach.res_id = msg.id
                attach.record_name = self.display_name

    def name_get(self):
        if self._context.get('dropDown', False):
            res = []
            for rec in self:
                name = rec.name
                res.append((rec.id, name))
            return res
        else:
            return super(ProductAttributeValue, self).name_get()

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_variant_price(self, product_id=False, pricelist=False):
        self.ensure_one()
        product_variant = self.product_variant_ids.filtered(lambda x: x.warranty_property_id.name == product_id.name)
        return {
            'price': product_variant.with_context({'pricelist':pricelist.id}).price if product_variant else 0
        }

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False,
                              parent_combination=False, only_template=False):
        res = super()._get_combination_info(combination, product_id, add_qty, pricelist, parent_combination, only_template)
        product_variant_id = self.env['product.product'].browse(res['product_id'])
        res[
            'product_variant_property_type_attribute_value_name'] = product_variant_id.product_template_attribute_value_ids.filtered(
            lambda x: x.attribute_id.name == "Property Type").name
        return res