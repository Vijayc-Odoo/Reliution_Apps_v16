# -*- coding: utf-8 -*-
# Part of Reliution Consulting Services.
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    remarks_for_purchase = fields.Text(string="Notes for Purchase")
    is_remarks_for_purchase = fields.Boolean(
        related="company_id.remark_for_purchase_order", string="Is Notes for Purchase")
