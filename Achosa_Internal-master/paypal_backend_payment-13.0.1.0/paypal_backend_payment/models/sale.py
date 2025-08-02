# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    due_amount = fields.Monetary(compute='compute_due_amount', string='Due Amount')

    def button_pay(self):
        self.ensure_one()
        order = self
        if order:
            transaction = self.env['payment.transaction']
            paypal = self.env['payment.acquirer'].search([('provider', '=', 'paypal')])
            token = paypal._paypal_s2s_get_access_token()
            name = order.name
            exst_trans = transaction.search([('sale_order_id', '=', order.id)])
            if exst_trans:
                name = order.name + 'x' + str(len(exst_trans) + 1)
            tx_values = {
                'acquirer_id': paypal.id,
                'reference': name,
                'amount': order.due_amount,
                'currency_id': order.currency_id.id,
                'partner_id': self.env.user.partner_id.id,
                'type': 'form',
                'sale_order_id': order.id,
            }
            return_url = transaction._paypal_s2s_send(tx_values, token)
            return return_url

    def compute_due_amount(self):
        for rec in self:
            transactions = self.env['payment.transaction'].search([('sale_order_id', '=', rec.id), ('state', '=', 'done')])
            rec.due_amount = rec.amount_total - sum(transactions.mapped('amount'))
