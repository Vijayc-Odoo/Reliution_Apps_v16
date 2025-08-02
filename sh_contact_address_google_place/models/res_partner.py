# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

import json

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sh_contact_google_location = fields.Char('Enter Location')
