import logging
import pprint
import re
from odoo import _, models, fields
from odoo.addons.payment import utils as payment_utils
from odoo.exceptions import UserError, ValidationError
from requests import request

from .. import const


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    paymob_transaction_id = fields.Char(string="Paymob Transaction Id")
    paymob_order_id = fields.Char(string="Paymob Order Id")

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return Paymob-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "paymob":
            return res

        intent = self._paymob_create_intent()

        client_secret = intent.get("client_secret")
        public_key = self.provider_id.paymob_public_key

        api_url = (
            self.provider_id._paymob_get_api_url()
            + f"unifiedcheckout/?publicKey={public_key}&clientSecret={client_secret}"
        )
        rendering_values = {}
        rendering_values = {
            "api_url": api_url,
            "public_key": public_key,
            "client_secret": client_secret,
        }
        if self.state_message:
            rendering_values["api_url"] = self.state_message
        return rendering_values

    def _get_specific_processing_values(self, processing_values):
        """Override of payment to return Paymob-specific processing values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != "paymob":
            return res

        if self.token_id:
            url = self._paymob_pay_with_token()
            processing_values["paymob_token_redirect_url"] = url
        return processing_values

    def _paymob_create_intent(self):
        """Create a payment intent with Paymob.
        :return: The intent and the redirection URL if a token is used.
        :rtype: tuple
        """
        if self.provider_code != "paymob":
            return

        base_url = self.provider_id._paymob_get_api_url()
        mixed_integrations = None

        if base_url == const.BASE_URL["omn"]:
            mixed_integrations = self._handle_omn_payment_payload_case(base_url)

        paymob_api_url = f"{base_url}v1/intention/"
        # headers
        headers = {
            "Authorization": f"Token {self.provider_id.paymob_secret_key}",
            "Content-Type": "application/json",
        }

        first_name, last_name = payment_utils.split_partner_name(self.partner_name)
        if not first_name and not last_name:
            raise UserError(
                "Please ensure that you have entered a valid name (first name and last name)."
            )

        card_token = []
        if self.token_id:
            token = (
                self.env["payment.token"]
                .sudo()
                .search(
                    [
                        ("id", "=", self.token_id.id),
                        ("partner_id", "=", self.partner_id.id),
                        ("payment_method_id", "=", self.payment_method_id.id),
                        ("active", "=", True),
                    ]
                )
            )
            if token:
                card_token = [t.paymob_reference for t in token]

        base_url = self.provider_id.get_base_url()
        if not base_url.endswith("/"):
            base_url += "/"

        notification_url = f"{base_url}payment/paymob/return"

        payload = {
            "amount": payment_utils.to_minor_currency_units(
                self.amount, self.currency_id
            ),
            "currency": self.currency_id.name,
            "payment_methods": [
                *(
                    mixed_integrations
                    if mixed_integrations
                    else [self.payment_method_id.integration_id]
                )
            ],
            "card_tokens": card_token,
            "billing_data": {
                "first_name": first_name or ".",
                "last_name": last_name or ".",
                "street": self.partner_address or "",
                "phone_number": re.sub(r"[^\d]", "", self.partner_id.mobile)
                or re.sub(r"[^\d]", "", self.partner_id.phone),
                "city": self.partner_city or "",
                "country": self.partner_country_id.code or "",
                "email": self.partner_email or "",
                "state": self.partner_state_id.name or "",
            },
            "extras": {
                "transaction_reference": self.reference,
            },
            "notification_url": notification_url,
        }
        if not self.provider_id.paymob_hmac:
            _logger.error("Paymob HMAC key is not set, won't create intent")
            raise UserError("Failed to create Paymob transaction. Please try again.")

        response = request("POST", paymob_api_url, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code != 201:
            _logger.error(
                "Paymob intent creation failed: %s", pprint.pformat(response_data)
            )
            if response_data.get("billing_data"):
                try:
                    errors = []
                    for field, messages in response_data["billing_data"].items():
                        for message in messages:
                            errors.append(
                                f"{field.replace('_', ' ').capitalize()}: {message}"
                            )

                    error_message = "\n".join(errors)
                    raise UserError(error_message)
                except KeyError:
                    _logger.error("Paymob: received unknown data: %s", response_data)
                    pass
            raise UserError(
                f"Failed to create Paymob transaction. Please try again. {next(iter(response_data.values()))[0]}"
            )

        _logger.info("Paymob intent response: %s", pprint.pformat(response_data))
        return response_data

    def _handle_omn_payment_payload_case(self, url):
        """
        Handle the case of payment payload for Oman.
        :return: Integration ID for MIGS.
        """
        if self.provider_code != "paymob":
            return

        gateway_type = self.payment_method_id.code
        if gateway_type != "OMANNET":
            return None

        auth_url = url + "api/auth/tokens"
        response = request(
            "POST", auth_url, json={"api_key": self.provider_id.paymob_api_key}
        )
        token = response.json().get("token")
        if response.status_code == 403 or not token:
            raise UserError("Something went wrong, please try again later.")

        payment_integrations_url = (
            url
            + "api/ecommerce/integrations?is_plugin=true&page_size=500&is_deprecated=false&is_standalone=false&is_next=yes"
        )
        response = request(
            "GET",
            payment_integrations_url,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code != 200:
            raise UserError("Something went wrong, please try again later.")
        response_data = response.json().get("results")
        oman_net_details = [
            item
            for item in response_data
            if item.get("id") == self.payment_method_id.integration_id
        ]
        if not oman_net_details:
            raise UserError("Something went wrong, please try again later.")
        oman_net_details = oman_net_details[0]

        migs_integrations = [
            item.get("id")
            for item in response_data
            if item.get("gateway_type") in ("MIGS", "VPC")
            and item.get("is_live") == oman_net_details.get("is_live")
        ]
        if not migs_integrations:
            raise UserError("Something went wrong, please try again later.")

        migs_integrations.append(oman_net_details.get("id"))
        return migs_integrations

    def _paymob_pay_with_token(self):
        """Pay with a token using Paymob.
        :return: The redirection URL.
        :rtype: str
        """

        intent = self._paymob_create_intent()

        payment_methods = intent.get("payment_methods")
        payment_method = None
        for method in payment_methods:
            if method.get("integration_id") == self.payment_method_id.integration_id:
                payment_method = method
                break
        if not payment_method:
            raise ValidationError("Something went wrong, Please try again")
        method_type = payment_method.get("method_type")
        use_cvc_with_moto = payment_method.get("use_cvc_with_moto")

        if method_type != "moto" or use_cvc_with_moto == True:
            client_secret = intent.get("client_secret")
            public_key = self.provider_id.paymob_public_key

            redirection_url = (
                self.provider_id._paymob_get_api_url()
                + f"unifiedcheckout/?publicKey={public_key}&clientSecret={client_secret}"
            )

            return redirection_url

        elif method_type == "moto":
            base_url = self.provider_id._paymob_get_api_url()
            paymob_api_url = f"{base_url}api/acceptance/payments/pay"

            headers = {
                "Authorization": f"Token {self.provider_id.paymob_secret_key}",
            }

            payment_key = None
            for key in intent.get("payment_keys"):
                if key.get("integration") == self.payment_method_id.integration_id:
                    payment_key = key.get("key")
                    break

            payload = {
                "source": {
                    "identifier": self.token_id.paymob_reference,
                    "subtype": "TOKEN",
                },
                "payment_token": payment_key,
            }

            response = request("POST", paymob_api_url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code != 200:
                _logger.error(
                    "Paymob moto payment failed: %s", pprint.pformat(response_data)
                )
                self._set_error(state_message=_("The payment failed."))
                raise UserError(
                    "Failed to create Paymob transaction. Please try again."
                )

            # States are from response are strings not booleans
            self.provider_reference = response_data.get("id")
            if response_data.get("pending") == "true":
                self._set_pending(state_message=_("The payment is pending."))
            elif response_data.get("is_auth") == "true":
                self._set_authorized(state_message=_("The payment is authorized."))
            elif response_data.get("error_occured") == "true":
                self._set_error(state_message=_("The payment failed."))
            elif response_data.get("success") == "true":
                self._set_done()
            else:
                _logger.error("Paymob: received unknown data: %s", response_data)
                raise UserError(
                    "Failed to create Paymob transaction. Please try again."
                )

            return response_data["redirection_url"]
        else:
            _logger.error("Paymob: received unknown data: %s", intent)
            raise UserError("Failed to create Paymob transaction. Please try again.")

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction based on Paymob data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data were received.
        :raise ValidationError: If the data match no transaction.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "paymob" or len(tx) == 1:
            return tx

        try:
            reference = notification_data["obj"]["payment_key_claims"]["extra"][
                "transaction_reference"
            ]
            tx = self.search(
                [("reference", "=", reference), ("provider_code", "=", "paymob")]
            )

            if not tx:
                _logger.error(
                    "Paymob: received data for reference %s; no order found", reference
                )
                raise ValidationError(
                    _("Paymob: Unable to find the transaction form call back data.")
                )
        except KeyError:
            _logger.error("Paymob: received data without transaction reference")
            raise ValidationError(
                _("Paymob: received data without transaction reference")
            )

        return tx

    def _process_notification_data(self, notification_data):
        """Override of `payment` to process the transaction based on Paymob data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data were received.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "paymob":
            return

        if not notification_data:
            _logger.error("Paymob: received empty data")
            self._set_canceled(state_message=_("The customer left the payment page."))
            return

        # update the transaction data if the call back is from shopify
        try:
            if (
                notification_data["obj"].get("payment_key_claims")
                and notification_data["obj"]
                .get("payment_key_claims")["extra"]
                .get("api_source")
                == "SHOPIFY"
            ):
                try:
                    # updating partner data
                    if notification_data["obj"]["payment_key_claims"][
                        "billing_data"
                    ].get("first_name") and notification_data["obj"][
                        "payment_key_claims"
                    ][
                        "billing_data"
                    ].get(
                        "last_name"
                    ):
                        self.partner_name = (
                            notification_data["obj"]["payment_key_claims"][
                                "billing_data"
                            ].get("first_name")
                            + " "
                            + notification_data["obj"]["payment_key_claims"][
                                "billing_data"
                            ].get("last_name")
                        )
                    self.partner_phone = notification_data["obj"]["payment_key_claims"][
                        "billing_data"
                    ].get("phone_number")
                    self.partner_email = notification_data["obj"]["payment_key_claims"][
                        "billing_data"
                    ].get("email")
                    self.partner_city = notification_data["obj"]["payment_key_claims"][
                        "billing_data"
                    ].get("city")

                    self.provider_code = "paymob"
                    self.provider_reference = notification_data.get("obj").get("id")

                    # updating the payment method
                    payment_method_id = (
                        self.env["payment.method"]
                        .sudo()
                        .search(
                            [
                                (
                                    "integration_id",
                                    "=",
                                    notification_data["obj"]["integration_id"],
                                ),
                                "|",
                                ("active", "=", True),
                                ("active", "=", False),
                            ]
                        )
                        .id
                    )
                    if payment_method_id:
                        self.payment_method_id = payment_method_id

                    # updating the provider id
                    provider_id = (
                        self.env["payment.provider"]
                        .sudo()
                        .search(
                            [
                                ("code", "=", "paymob"),
                            ]
                        )
                        .id
                    )
                    if provider_id:
                        self.provider_id = provider_id

                    self._set_done()
                except Exception as e:
                    _logger.error(
                        "Error while updating the transaction data from shopify call back data: %s",
                        e,
                    )
                    self._set_error(
                        state_message=_("Shopify call back data is not valid.")
                    )
        except Exception as e:
            _logger.error(
                "Error while updating the transaction data from shopify call back data: %s",
                e,
            )
            pass

        # Updating state of the transaction based on the notification data
        self.provider_reference = notification_data["obj"]["id"]
        data = notification_data["obj"]
        if data["success"]:
            if data["pending"]:
                _logger.info(
                    "Transaction with reference %s and transaction id %s is pending",
                    self.reference,
                    self.provider_reference,
                )
                self._set_pending(state_message=_("The payment is pending."))
            elif data["is_auth"] and not data["is_captured"] and not data["is_voided"]:
                _logger.info(
                    "Transaction with reference %s and transaction id %s is authorized",
                    self.reference,
                    self.provider_reference,
                )
                self._set_authorized(state_message=_("The payment is authorized."))
            elif data["is_captured"] and data.get("captured_amount") == data.get(
                "amount_cents"
            ):
                _logger.info(
                    "Transaction with reference %s and transaction id %s is captured",
                    self.reference,
                    self.provider_reference,
                )
                self._set_done()
            elif data["is_captured"] and data.get("captured_amount") < data.get(
                "amount_cents"
            ):
                _logger.info(
                    "Transaction with reference %s and transaction id %s is partially captured",
                    self.reference,
                    self.provider_reference,
                )
                self._set_authorized(state_message=_("The payment is authorized."))
            elif data["is_voided"]:
                _logger.info(
                    "Transaction with reference %s and transaction id %s is voided",
                    self.reference,
                    self.provider_reference,
                )
                self._set_canceled(state_message=_("The payment was voided."))
            elif data["is_refunded"]:
                _logger.info(
                    "Transaction with reference %s and transaction id %s is refunded",
                    self.reference,
                    self.provider_reference,
                )
                self._set_done()
            elif data["is_auth"] == False:
                _logger.info(
                    "Transaction with reference %s and transaction id %s is done",
                    self.reference,
                    self.provider_reference,
                )
                self._set_done()
            else:
                _logger.error("Paymob: received unknown data: %s", data)
                self._set_error(state_message=_("The payment failed."))

        elif data["error_occured"]:
            _logger.error(
                "Transaction with reference %s and transaction id %s failed",
                self.reference,
                self.provider_reference,
            )
            _logger.error("Paymob: received error data: %s", data)
            self._set_error(state_message=_("The payment failed."))
        elif data["pending"]:
            self._set_pending(state_message=_("The payment is pending."))
        else:
            _logger.error(
                "Transaction with reference %s and transaction id %s failed",
                self.reference,
                self.provider_reference,
            )
            _logger.error("Paymob: received unknown data: %s", data)
            self._set_error(state_message=_("The payment failed."))

    def _send_capture_request(self, amount_to_capture=None):
        """Override of `payment` to send a capture request to Paymob."""
        child_capture_tx = super()._send_capture_request(
            amount_to_capture=amount_to_capture
        )
        if self.provider_code != "paymob":
            return child_capture_tx

        url = self.provider_id._paymob_get_api_url() + "api/acceptance/capture"
        headers = {
            "Authorization": f"Token {self.provider_id.paymob_secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        payload = {
            "transaction_id": self.provider_reference,
        }

        response = request("POST", url, data=payload, headers=headers)
        response_data = response.json()

        _logger.info(
            "Paymob capture request for transaction with reference %s response is %s",
            self.reference,
            pprint.pformat(response_data),
        )
        if response.status_code != 201 or response_data.get("error_occured"):
            _logger.error(
                "Paymob capture request failed: %s", pprint.pformat(response_data)
            )
            raise UserError("Failed to capture Paymob transaction. Please try again.")
        child_capture_tx.provider_reference = response.json().get("id")
        self.env.ref("payment.cron_post_process_payment_tx")._trigger()
        return child_capture_tx

    def _send_void_request(self, amount_to_void=None):
        """Override of `payment` to send a void request to Paymob."""
        child_void_tx = super()._send_void_request(amount_to_void=amount_to_void)
        if self.provider_code != "paymob":
            return child_void_tx

        url = self.provider_id._paymob_get_api_url() + "api/acceptance/void_refund/void"
        headers = {
            "Authorization": f"Token {self.provider_id.paymob_secret_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "transaction_id": self.provider_reference,
        }

        response = request("POST", url, json=payload, headers=headers)
        response_data = response.json()
        _logger.info(
            "Paymob void request for transaction with reference %s response is %s",
            self.reference,
            pprint.pformat(response_data),
        )

        if response.status_code != 201 or response_data.get("error_occured"):
            _logger.error(
                "Paymob void request failed: %s", pprint.pformat(response_data)
            )
            if response.json().get("message") == "Transaction is already voided":
                self.env.ref("payment.cron_post_process_payment_tx")._trigger()
                raise UserError("The transaction is already voided.")
            raise UserError("Failed to void Paymob transaction. Please try again.")

        child_void_tx.provider_reference = response.json().get("id")
        self.env.ref("payment.cron_post_process_payment_tx")._trigger()

        return child_void_tx

    def _send_refund_request(self, amount_to_refund=None):
        """Override of payment to send a refund request to Paymob.

        Note: self.ensure_one()

        :param float amount_to_refund: The amount to refund.
        :return: The refund transaction created to process the refund request.
        :rtype: recordset of `payment.transaction`
        """
        refund_tx = super()._send_refund_request(amount_to_refund=amount_to_refund)
        if self.provider_code != "paymob":
            return refund_tx

        url = (
            self.provider_id._paymob_get_api_url() + "api/acceptance/void_refund/refund"
        )
        headers = {"Authorization": f"Token {self.provider_id.paymob_secret_key}"}
        payload = {
            "amount_cents": payment_utils.to_minor_currency_units(
                amount_to_refund, self.currency_id
            ),
            "transaction_id": self.provider_reference,
        }

        response = request("POST", url, json=payload, headers=headers)
        response_data = response.json()
        _logger.info(
            "Paymob refund request for transaction with reference %s response is %s",
            self.reference,
            pprint.pformat(response_data),
        )

        if response.status_code == 201:
            refund_tx._handle_notification_data("paymob", {"obj": response_data})
            self.env.ref("payment.cron_post_process_payment_tx")._trigger()
            return refund_tx

        elif response.json().get("message") == "Full Amount has been already refunded":
            _logger.error(
                "Paymob refund request failed: %s", pprint.pformat(response_data)
            )
            self.env.ref("payment.cron_post_process_payment_tx")._trigger()
            raise UserError("The full amount has already been refunded.")
        else:
            _logger.error(
                "Paymob refund request failed: %s", pprint.pformat(response_data)
            )
            raise UserError("Failed to refund Paymob transaction. Please try again.")
