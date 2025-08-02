# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class CountryState(models.Model):
    _inherit = 'res.country.state'

    enable_home_warranty = fields.Boolean("Show in home warranty")