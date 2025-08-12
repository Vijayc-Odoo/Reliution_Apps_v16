# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class FetchIncomingMail(models.Model):
    _name = 'fetch.incoming.mail'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Fetching Incoming Mail'

    email = fields.Char(string='Email')
    name = fields.Char('Title', index="trigram")
    subject = fields.Char('Subject', index="trigram")



