# -*- coding: utf-8 -*-

from odoo import fields, models


class MailAttachment(models.TransientModel):
    """This model is used for handling mail attachments in Odoo."""
    _name = "mail.attachment"
    _description = "Mail Attachment"

    mail_attachment = fields.Binary(string="Attachment",
                                    help="Binary field to store the attachment"
                                         " data.")
    file_name = fields.Char(string="File Name",
                            help="Name of the attached file.")
