import logging
from odoo import models

_logger = logging.getLogger("##### Achosa #####")


class IrLogging(models.Model):
    _inherit = 'ir.logging'

    def create_ir_logging_record(self, function_name, message, path):
        """
            Usage: This method creates the ir.logging record
        """
        values = {
            'name': 'Achosa',
            'type': 'server',
            'level': 'info',
            'dbname': self.env.cr.dbname,
            'message': message,
            'func': function_name,
            'path': path,
            'line': '0',
        }
        _logger.info(f"IR LOGGING INFO: {values}")
        self.sudo().create(values)
