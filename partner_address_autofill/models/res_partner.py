# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

import json
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    rcs_contact_google_location = fields.Char('Enter Location')
