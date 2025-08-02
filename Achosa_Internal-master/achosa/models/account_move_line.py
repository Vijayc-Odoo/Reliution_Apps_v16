from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def reconcile(self):
        results = super(AccountMoveLine, self).reconciled()
        for move_id in self.move_id.filtered(lambda  move: move.payment_state in ('paid')):
            pass
        return results