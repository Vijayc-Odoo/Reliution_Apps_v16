# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"
    
    state_ids = fields.Many2many(comodel_name='res.country.state', string='States')

    def get_home_warranty_pricelist(self, state_id):
        return self.env['product.pricelist'].search([('state_ids', '=', state_id.id)], limit=1)

    def get_home_warranty_pricelist_by_state_wise(self, state_id):
        pricelist_id = self.get_home_warranty_pricelist(state_id).id if state_id else False
        if not pricelist_id:
            pricelist_id = self.env.ref("product.list0").id
        return pricelist_id
