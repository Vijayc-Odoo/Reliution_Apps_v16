# -*- coding: utf-8 -*-
# Part of Reliution Consulting Services.
from odoo import fields, models


class RcsResCompany(models.Model):
    _inherit = 'res.company'

    purchase_order_backdate = fields.Boolean(
        "Enable Custom Date for Purchase Orders")
    rcs_notes_for_purchase_order = fields.Boolean(
        "Enable Purchase Order Notes")
    rcs_notes_mandatory_for_purchase_order = fields.Boolean(
        "Require Notes for Purchase Orders")
    bill_backdate = fields.Boolean("Sync Bill Date with Purchase Order Date")
    stock_move_backdate = fields.Boolean("Sync Receipt Date with Purchase Order Date ")


class RcsResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_order_backdate = fields.Boolean(
        "Enable Custom Date for Purchase Orders", related="company_id.purchase_order_backdate", readonly=False)
    rcs_notes_for_purchase_order = fields.Boolean(
        "Enable Purchase Order Notes", related="company_id.rcs_notes_for_purchase_order", readonly=False)
    rcs_notes_mandatory_for_purchase_order = fields.Boolean(
        "Require Notes for Purchase Orders", related="company_id.rcs_notes_mandatory_for_purchase_order", readonly=False)
    bill_backdate = fields.Boolean(
        "Sync Bill Date with Purchase Order Date", related="company_id.bill_backdate", readonly=False)
    stock_move_backdate = fields.Boolean(
        "Sync Receipt Date with Purchase Order Date", related="company_id.stock_move_backdate", readonly=False)
