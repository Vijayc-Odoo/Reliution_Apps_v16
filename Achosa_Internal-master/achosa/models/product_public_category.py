from odoo import api, fields, models, tools, _


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    state_id = fields.Many2one("res.country.state", "States")
