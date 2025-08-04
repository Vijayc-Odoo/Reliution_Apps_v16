# -*- coding: utf-8 -*-

from odoo import fields, models

class ResCompany(models.Model):
    _inherit = "res.company"

    model_selection_for_email = fields.Many2many("ir.model",string="Model Selection For Email")

class ResConfigSettings(models.TransientModel):
    """This model extends the 'res.config.settings' model in Odoo to add
    additional settings."""
    _inherit = "res.config.settings"

    def _default_mail_icon_id(self):
        """Method to return default mail_icon model """
        return self.env['mail.icon'].search([], order='id desc', limit=1)

    mail_icon_id = fields.Many2one("mail.icon",
                                   default=_default_mail_icon_id,
                                   ondelete='cascade',
                                   string="Mail Icon Id",
                                   help="Mail Icon Id")
    icon = fields.Binary('mail_icon',
                         related='mail_icon_id.mail_icon',
                         readonly=False,
                         help="Icon")
    custom_mail_logo = fields.Boolean(string="Custom Mail Logo",
                                      help="Customize your mail logo",
                                      config_parameter="odoo_mail_management."
                                                       "custom_mail_logo")

    model_selection_for_email = fields.Many2many("ir.model",related="company_id.model_selection_for_email",string="Model Selection For Email",readonly=False)

