import logging
from datetime import date, timedelta
from odoo import models

_logger = logging.getLogger("##### Achosa #####")


class MailMessage(models.Model):
    _inherit = "mail.message"

    def _prepare_achosa_mail_template_domain(self, model_name, resource_id, subject):
        return [['model', '=', model_name], ['res_id', '=', resource_id], ['subject', '=', subject]]

    def _get_achosa_mail_compose_message(self, model_name, resource_id, template_id, extra_):
        domain = [['model', '=', model_name], ['res_id', '=', resource_id], ['template_id', '=', template_id.id]]
        if extra_domain:
            domain.extend(extra_domain)
        return self.env['mail.compose.message'].search(extra_domain, limit=1)

    def _prepare_achosa_mail_domain(self, model_name, resource_id, template_id, **kwargs):
        search_mail_on_specific_date = kwargs.get('search_mail_on_specific_date', False) or False
        if search_mail_on_specific_date:
            today = date.today()
            to_date = kwargs.get('to_date', today) or today
            security_days = kwargs.get('security_days', 3) or 3
            default_from_date = to_date - timedelta(days=security_days)
            from_date = kwargs.get('from_date', default_from_date) or default_from_date
            domain = [['create_date', '>=', from_date], ['create_date', '<=', to_date]]
            mail_compose_message_id = self._get_achosa_mail_compose_message(model_name, resource_id, template_id,
                                                                            extra_domain=domain)
            domain.extend(
                self._prepare_achosa_mail_template_domain(model_name, resource_id, mail_compose_message_id.subject))
        else:
            mail_compose_message_id = self._get_achosa_mail_compose_message(model_name, resource_id, template_id,
                                                                            extra_)
            domain = self._prepare_achosa_mail_template_domain(model_name, resource_id, mail_compose_message_id.subject)
        _logger.info(f"Method: [_prepare_achosa_mail_domain], Domain: [{domain}]")
        return domain

    def search_achosa_existing_mail(self, model_name, resource_id, template_id, **kwargs):
        return self.search(
            self._prepare_achosa_mail_domain(model_name=model_name, resource_id=resource_id, template_id=template_id,
                                             **kwargs))
