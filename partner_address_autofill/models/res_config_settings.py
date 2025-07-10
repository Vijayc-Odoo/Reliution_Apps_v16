# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    # company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)

    rcs_is_enable_google_api_key = fields.Boolean(related="company_id.rcs_is_enable_google_api_key",string="Enable Google API",readonly=False)
    rcs_google_api_key = fields.Char(related="company_id.rcs_google_api_key",string="Key",readonly=False)
    rcs_google_api_search_char = fields.Integer(related="company_id.rcs_google_api_search_char" ,string="Search Charactor",readonly=False)
