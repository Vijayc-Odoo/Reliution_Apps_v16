# -*- coding: utf-8 -*-
import logging
import datetime
import pprint
from odoo import _, models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.addons.payment import utils as payment_utils
from requests import request

_logger = logging.getLogger(__name__)


class InheritPaymentLinkWizard(models.TransientModel):
    _inherit = "payment.link.wizard"

    @api.depends("amount", "currency_id", "partner_id", "company_id")
    def _compute_link(self):
        if self._context.get("using_paymob"):
            for payment_link in self:
                related_document = self.env[payment_link.res_model].browse(
                    payment_link.res_id
                )
                self._prepare_query_params(related_document)

                # Retrieve Paymob account details
                provider_id = self.env['payment.provider'].search([('code', '=', 'paymob')], limit=1)
                base_url = provider_id._paymob_get_api_url()
                paymob_api_url = f"{base_url}v1/intention/"

                # Headers for Paymob API
                headers = {
                    "Authorization": f"Token {provider_id.paymob_secret_key}",
                    "Content-Type": "application/json",
                }

                # Prepare payload with customer data
                first_name, last_name = payment_utils.split_partner_name(payment_link.partner_id.name)
                payload = {
                    "amount": payment_utils.to_minor_currency_units(payment_link.amount, payment_link.currency_id),
                    "currency": payment_link.currency_id.name,
                    "payment_methods": [provider_id.payment_method_ids[0].integration_id],
                    "billing_data": {
                        "first_name": first_name or ".",
                        "last_name": last_name or ".",
                        "phone_number": payment_link.partner_id.mobile or payment_link.partner_id.phone,
                        "country": payment_link.partner_id.country_id.code or "",
                        "email": payment_link.partner_id.email or "",
                        "state": payment_link.partner_id.state_id.name or "",
                    },
                }

                # Check if HMAC key is set for Paymob
                if not provider_id.paymob_hmac:
                    _logger.error("Paymob HMAC key is not set, won't create intent")
                    raise UserError("Failed to create Paymob transaction. Please try again.")

                # Send request to Paymob API to create the payment intent
                response = request("POST", paymob_api_url, json=payload, headers=headers)
                _logger.info("Get Payment Link details: %s", response.text)
                response_data = response.json()

                # Handle response and check for errors
                if response.status_code != 201:
                    _logger.error("Paymob intent creation failed: %s", pprint.pformat(response_data))
                    raise UserError("Failed to create Paymob transaction. Please try again.")

                # Extract details from the response
                intent = response_data
                client_secret = intent.get("client_secret")
                public_key = provider_id.paymob_public_key
                api_url = f"{provider_id._paymob_get_api_url()}unifiedcheckout/?publicKey={public_key}&clientSecret={client_secret}"
                payment_link.link = api_url

                total_amount = payment_link.amount
                invoice_id = False
                if payment_link.res_model == "account.move":
                    invoice_id = self.env[payment_link.res_model].browse(
                        payment_link.res_id
                    )

                payment_transaction = self.env["payment.transaction"].create(
                    {
                        "reference": invoice_id.name,
                        "amount": total_amount,
                        "currency_id": self.currency_id.id,
                        "provider_id": provider_id.id,
                        "payment_method_id": provider_id.payment_method_ids[0].id,
                        "create_date": datetime.datetime.now(),
                        "last_state_change": datetime.datetime.now(),
                        "partner_id": self.partner_id.id,
                        "partner_email": self.partner_id.email or "",
                        "partner_phone": self.partner_id.mobile
                        or self.partner_id.phone
                        or self.partner_id.whatsapp_number,
                        "invoice_ids": [(4, invoice_id.id)],
                    }
                )
        else:
            # If the context doesn't have 'using_paymob', call the original method
            super(InheritPaymentLinkWizard, self)._compute_link()
