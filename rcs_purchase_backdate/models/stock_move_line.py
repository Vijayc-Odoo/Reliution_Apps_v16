# -*- coding: utf-8 -*-
# Part of Reliution Consulting Services.
from odoo import fields, models


class RcsStockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    rcs_notes_for_purchase = fields.Text(
        string="Notes for Purchase", related="move_id.rcs_notes_for_purchase")
    is_rcs_notes_for_purchase = fields.Boolean(
        related="company_id.rcs_notes_for_purchase_order", string="Is Notes for Purchase")
