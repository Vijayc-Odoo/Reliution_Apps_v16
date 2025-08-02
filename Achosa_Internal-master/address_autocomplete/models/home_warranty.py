# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
""" Inherit existing model and Added/Manage the new functionality"""
from odoo import fields, models


class HomeWarranty(models.Model):
    """
        Added/Manage the new functionality
    """
    _inherit = "home.warranty"

    # Override the field and added the help, Ticket: [AO-640]
    property_street = fields.Char("Street",
                                  tracking=True,
                                  help="Having trouble finding the address?  Try removing the state, "
                                       "or if you have not already added it, add the state and see if that helps!")
