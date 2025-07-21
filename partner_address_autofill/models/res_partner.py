# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

import json
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    rcs_contact_google_location = fields.Char('Enter Location Somthing')
    test_field = fields.Char('Test Field')

class TestClass(models.Model):
    _inherit = 'crm.lead'

    test_field1 = fields.Char('Test Field As a Location')
