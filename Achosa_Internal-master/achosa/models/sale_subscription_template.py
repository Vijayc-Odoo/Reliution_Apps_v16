from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime
import datetime


class SaleSubscriptionTemplate(models.Model):

    _inherit = ['sale.subscription.template']

    trade_call_fee = fields.Char(string="Trade Call Fee")
    
    payment_mandatory = fields.Boolean(string="Automatic Payment")