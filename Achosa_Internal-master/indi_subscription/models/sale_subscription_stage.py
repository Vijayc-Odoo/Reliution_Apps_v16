# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleSubscriptionStage(models.Model):
    _inherit = "sale.subscription.stage"

    in_cancelled = fields.Boolean(string='In Cancelled', default=False, copy=False)
