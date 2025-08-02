# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    sh_is_enable_google_api_key = fields.Boolean(related="company_id.sh_is_enable_google_api_key",string="Enable Google API",readonly=False)
    sh_google_api_key = fields.Char(related="company_id.sh_google_api_key",string="Key",readonly=False)
