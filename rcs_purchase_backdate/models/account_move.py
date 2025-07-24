# -*- coding: utf-8 -*-
# Part of Reliution Consulting Services.
from odoo import fields, models


class RcsAccountMove(models.Model):
    _inherit = 'account.move'

    rcs_notes_for_purchase = fields.Text(string="Notes for Purchase")
    is_rcs_notes_for_purchase = fields.Boolean(
        related="company_id.rcs_notes_for_purchase_order", string="Is Notes for Purchase")
