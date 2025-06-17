from odoo import fields, models, api
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class PaymentMethod(models.Model):
    _inherit = "payment.method"

    description = fields.Text(string="Description")
    integration_id = fields.Integer(string="Integration ID")

    @api.model
    def write(self, vals):
        for record in self:
            if record.integration_id and "active" in vals:
                record.update_plugin_integration_ids(vals)

        return super(PaymentMethod, self).write(vals)

    def update_plugin_integration_ids(record, vals):
        """Get all payment methods related to the Paymob provider."""
        paymob_provider = record.env["payment.provider"].search(
            [("code", "=", "paymob")], limit=1
        )
        paymob_methods = set()
        if vals.get("active"):
            paymob_methods.add(record.integration_id)
        if paymob_provider:
            for method in paymob_provider.payment_method_ids:
                if method.active and record.integration_id != method.integration_id:
                    paymob_methods.add(method.integration_id)

        auth_token_url = f"{paymob_provider._paymob_get_api_url()}api/auth/tokens"
        response = requests.post(
            auth_token_url, json={"api_key": paymob_provider.paymob_api_key}
        )
        if response.status_code != 201:
            raise UserError("Failed to get auth token")

        auth_token = response.json().get("token")

        base_url = paymob_provider.get_base_url()

        headers = {"Authorization": f"Bearer {auth_token}"}

        payload = {
            "url": base_url,
            "is_ssl": True,
            "platform": "ODOO",
            "platform_version": "18.0",
            "plugin_version": "18.0",
            "selected_integrations": list(paymob_methods),
            "info": {"key": "value"},
        }

        _logger.info(
            f"Updating plugin integration ids for Paymob provider with payload: {payload}"
        )

        response = requests.post(
            f"{paymob_provider._paymob_get_api_url()}api/ecommerce/plugins",
            json=payload,
            headers=headers,
        )
        if response.status_code not in [200, 201, 202, 204]:
            _logger.error(
                f"Failed to update plugin integration ids for Paymob provider with response: {response.text}"
            )
            raise UserError("Failed to update plugin integration ids, please try")
        _logger.info(
            f"Successfully updated plugin integration ids for Paymob provider with response: {response.text}"
        )

        base_url = paymob_provider.get_base_url()
        if base_url and not base_url.endswith("/"):
            base_url += "/"

        if record.integration_id and vals.get("active"):
            payload = {
                "transaction_processed_callback": f"{base_url}payment/paymob/return",
                # "transaction_response_callback": f"{base_url}paymob/payment/done",
            }

            integrations_url = (
                paymob_provider._paymob_get_api_url()
                + f"api/ecommerce/integrations/{record.integration_id}"
            )
            response = requests.patch(integrations_url, headers=headers, json=payload)
            if response.status_code != 201:
                _logger.error(
                    f"Failed to update plugin integrations for Paymob provider with response: {response.json()}"
                )
                raise UserError(
                    "Failed to update plugin integrations, please try again"
                )
            _logger.info(
                f"Successfully updated integration webhook urls: {response.json()}"
            )
