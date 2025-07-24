# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class MailFolder(models.Model):
    _name = 'mail.folder'
    _description = 'Mail Folder'
    name = fields.Char(string="Name")

class MailTag(models.Model):
    _name = 'mail.tag'
    _description = 'Mail Tag'
    name = fields.Char(string="Name")

