# -*- coding: utf-8 -*-

from odoo import api, models


class IrAttachment(models.Model):
    """
    This model extends the functionality of 'ir.attachment' in Odoo.
    """
    _inherit = 'ir.attachment'

    @api.model
    def get_fields(self, value):
        """
        Retrieve specified fields from attachments identified by the given list of IDs.
        """
        data_list = []
        for values in value:
            attach = self.env['ir.attachment'].browse(values)
            data_dict = {
                'attachment': attach.id,
                'datas': attach.datas,
                'mimetype': attach.mimetype,
                'name': attach.name
            }
            data_list.append(data_dict)
        return data_list
