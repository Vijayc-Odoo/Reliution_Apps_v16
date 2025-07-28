# -*- coding: utf-8 -*-
# Part of Reliution Consulting Services.
from odoo import fields, models


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    notes_for_purchase = fields.Text(string="Notes for Purchase")
    is_notes_for_purchase = fields.Boolean(
        related="company_id.notes_for_purchase_order", string="Is Notes for Purchase")
