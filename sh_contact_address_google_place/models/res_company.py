# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sh_is_enable_google_api_key = fields.Boolean(string="Enable Google API")
    sh_google_api_key = fields.Char(string="Key")
