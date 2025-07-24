# -*- coding: utf-8 -*-
# Part of Reliution Consulting Services.
from odoo import models, fields, api
from datetime import date, datetime


class BackdateWizard(models.TransientModel):
    _name = 'rcs.purchase.backdate.wizard'
    _description = "Purchase Backdate Wizard"

    purchase_order_ids = fields.Many2many('purchase.order')
    date_planned = fields.Datetime(
        string="Receipt Date", required=True, default=datetime.now())
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    rcs_notes = fields.Text(string="Notes")
    is_rcs_notes = fields.Boolean(
        related="company_id.rcs_notes_for_purchase_order", string="Is Notes")
    is_rcs_notes_mandatory = fields.Boolean(
        related="company_id.rcs_notes_mandatory_for_purchase_order", string="Is Notes mandatory")
    is_boolean = fields.Boolean()

    backdate_for_stock_move=fields.Boolean("Receipt BackDate")
    backdate_for_bill=fields.Boolean("Bill BackDate")



    @api.onchange('date_planned')
    def onchange_date_planned(self):
        if self.date_planned:
            if str(self.date_planned.date()) < str(date.today()):
                self.is_boolean = True
            else:
                self.is_boolean = False

    def open_rcs_backdate_wizard(self):
        active_ids = self.env.context.get('active_ids')

        return {
            'name': 'Assign Backdate',
            'res_model': 'rcs.purchase.backdate.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('rcs_purchase_backdate.purchase_order_backdate_wizard_view_form').id,
            'context': {
                    'default_purchase_order_ids': [(6, 0, active_ids)],
            },
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def assign_backdate(self):

        for purchase_order in self.purchase_order_ids:

            if self.company_id.purchase_order_backdate:
                purchase_order.write({
                    'date_planned': self.date_planned,
                    'date_approve': self.date_planned,
                    'rcs_notes': self.rcs_notes if self.rcs_notes else ''
                })

            if self.backdate_for_bill:
                for bill in purchase_order.invoice_ids:
                    bill.name = False
                    bill.invoice_date = self.date_planned
                    bill.date = self.date_planned
                    bill.rcs_notes_for_purchase = self.rcs_notes if self.rcs_notes else ''

            if self.backdate_for_stock_move:
                for picking in purchase_order.picking_ids:
                    picking.scheduled_date = self.date_planned
                    picking.date_done = self.date_planned
                    picking.rcs_notes_for_purchase = self.rcs_notes if self.rcs_notes else ''

                    stock_moves = self.env['stock.move'].search(
                        [('picking_id', '=', picking.id)])
                    product_moves = self.env['stock.move.line'].search(
                        [('move_id', 'in', stock_moves.ids)])

                    account_moves = self.env['account.move'].search(
                        [('stock_move_id', 'in', stock_moves.ids)])
                    valuation_layers = self.env['stock.valuation.layer'].search(
                        [('stock_move_id', 'in', stock_moves.ids)])

                    for account_move in account_moves:
                        account_move.button_draft()
                        account_move.name = '/'
                        account_move.date = self.date_planned
                        account_move.action_post()

                    for move in stock_moves:
                        move.date = self.date_planned
                        move.rcs_notes_for_purchase = self.rcs_notes if self.rcs_notes else ''

                    for move in product_moves:
                        move.date = self.date_planned

                    for layer in valuation_layers:
                        self.env.cr.execute("""
                            Update stock_valuation_layer set create_date='%s' where id=%s;
                        """ % (self.date_planned, layer.id))
