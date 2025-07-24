# -*- coding: utf-8 -*-
# Part of Reliution Consulting Services.
from odoo import fields, models, api


class RcsStockPicking(models.Model):
    _inherit = 'stock.picking'

    rcs_notes_for_purchase = fields.Text(
        string="Notes for Purchase", related="purchase_id.rcs_notes")
    is_rcs_notes_for_purchase = fields.Boolean(
        related="company_id.rcs_notes_for_purchase_order", string="Is Notes for Purchase")
    
    def write(self, vals):
        for rec in self:
            if rec.purchase_id and 'date_done' in vals and rec.company_id.stock_move_backdate:
                vals['date_done'] = rec.purchase_id.date_approve
            return super().write(vals)

    def _set_scheduled_date(self):
        for picking in self:
            picking.move_ids.write({'date': picking.scheduled_date})
