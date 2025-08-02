import logging
from odoo import models

_LOGGER = logging.getLogger("##### Achosa #####")


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _onchange_template_id(self, template_id, composition_mode, model, res_id):
        result = super(MailComposer, self)._onchange_template_id(template_id, composition_mode, model, res_id)
        home_warranty_paid_template_id = self.env.ref('achosa.hw_paid', raise_if_not_found=False)
        if template_id and home_warranty_paid_template_id and template_id == home_warranty_paid_template_id.id and model=='account.move':
            model_record_id = self.env[model].browse(res_id)
            attachment_ids = home_warranty_paid_template_id.attachment_ids.ids.copy()
            if attachment_ids:
                attachment_ids.extend(model_record_id._get_attachment_ids(model_record_id.invoice_line_ids))
                template_attachment_ids = result.get('value', {}).get('attachment_ids', [])
                if template_attachment_ids and len(template_attachment_ids[0]) == 3:
                    attachment_ids = list(set(result['value']['attachment_ids'][0][-1] + attachment_ids))
                    result['value']['attachment_ids'] = [(6, 0, attachment_ids)]
                    _LOGGER.info(f"\n\n\n Result Attachments: {result['value']['attachment_ids']}\n\n\n")
        return result