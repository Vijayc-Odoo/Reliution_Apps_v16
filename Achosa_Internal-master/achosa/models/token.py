# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from datetime import datetime


class PaymentToken(models.Model):
    _inherit = "payment.token"
    
    # field to store home warranty
    remove_home_warranty = fields.Many2one("home.warranty", string="Home Warranty",
                                       help="Home Warranty, set by removal automation")
    
    # field to store removal batch
    remove_batch = fields.Char(string="Removal Batch",
                                       help="Removal Batch ID, see Database Logging")
    
    # Removal Status
    remove_status = fields.Selection([('Ready', 'Ready'), ('WarnHW','Warn Home Warranty Count'), ('WarnToken','Warn Token Count'),
                              ('Reviewed', 'Reviewed')], string="Removal Status",
                                       help="Removal Status")