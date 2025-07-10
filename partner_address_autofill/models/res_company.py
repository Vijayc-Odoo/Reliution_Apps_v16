# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    rcs_is_enable_google_api_key = fields.Boolean(string="Enable Google API")
    rcs_google_api_key = fields.Char(string="Key")
    rcs_google_api_search_char = fields.Integer(string="Search Charactor" , default=3)