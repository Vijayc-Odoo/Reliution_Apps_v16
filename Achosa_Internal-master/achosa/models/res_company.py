from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    add_on_attribute_value_non_owner = fields.Integer(string='NOOP Addon Id', default=0)
    add_on_attribute_value_conserve = fields.Integer(string='Conserve Addon Id', default=0)
    add_on_attribute_value_conserve_plus = fields.Integer(string='Conserve Plus Addon Id', default=0)
    estated_url = fields.Text(string="Estated URL")
    estated_token = fields.Text(string="Estated Token")
    authorize_login_test = fields.Text(string="Login (Test mode)")
    authorize_signature_key_test = fields.Text(string="Signature Key (Test mode)")
    authorize_transaction_key_test = fields.Text(string="Transaction Key (Test mode)")
    service_map_attachment_id = fields.Integer(string="Service Map Document ID")
    buyer_attachment_id = fields.Integer(string="Real Estate Buyer Document ID")
    buyer_idaho_attachment_id = fields.Integer(string="Real Estate Buyer Idaho Document ID")
    homeowner_attachment_id = fields.Integer(string="Homeowner Document ID")
    homeowner_idaho_attachment_id = fields.Integer(string="Homeowner Idaho Document ID")
    seller_attachment_id = fields.Integer(string="Real Estate Seller Document ID")

    service_map_attachment_name = fields.Char(string="Service Map Document Name")
    buyer_attachment_name = fields.Char(string="Real Estate Buyer Document Name")
    buyer_idaho_attachment_name = fields.Char(string="Real Estate Buyer Idaho Document Name")
    homeowner_attachment_name = fields.Char(string="Homeowner Document Name")
    homeowner_idaho_attachment_name = fields.Char(string="Homeowner Idaho Document Name")
    seller_attachment_name = fields.Char(string="Real Estate Seller Document Name")
