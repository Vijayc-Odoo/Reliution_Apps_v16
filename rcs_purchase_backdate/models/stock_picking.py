# -*- coding: utf-8 -*-
# Part of Reliution Consulting Services.
from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    remarks_for_purchase = fields.Text(
        string="Remarks for Purchase", related="purchase_id.remarks")
    is_remarks_for_purchase = fields.Boolean(
        related="company_id.remark_for_purchase_order", string="Is Remarks for Purchase")

    # @api.depends('move_ids.state', 'move_ids.date', 'move_type')
    # def _compute_scheduled_date(self):
    #     super()._compute_scheduled_date()
    #     for picking in self:
    #         if picking.company_id.backdate_for_stock_move:
    #             if picking.purchase_id.date_approve:
    #                 picking.scheduled_date = picking.purchase_id.date_approve
    
    def write(self, vals):
        for rec in self:
            if rec.purchase_id and 'date_done' in vals and rec.company_id.backdate_for_stock_move:
                vals['date_done'] = rec.purchase_id.date_approve

            return super().write(vals)

    def _set_scheduled_date(self):
        for picking in self:
            # if picking.state in ('done', 'cancel'):
            #     raise UserError(_("You cannot change the Scheduled Date on a done or cancelled transfer."))
            picking.move_ids.write({'date': picking.scheduled_date})
