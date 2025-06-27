import hashlib
import hmac
import json
import logging
import pprint
import re

import requests
from odoo import http
from odoo.http import request
from datetime import date

from .. import const

_logger = logging.getLogger(__name__)


class PaymobController(http.Controller):
    @http.route(
        "/payment/paymob/return",
        type="json",
        auth="public",
        csrf=False,
        methods=["POST", "GET"],
    )
    def paymob_return(self, **kwargs):
        raw_data = request.httprequest.get_data()

        try:
            json_data = json.loads(raw_data)
        except json.JSONDecodeError:
            _logger.error("Invalid JSON data received.")
            return {"error": "Invalid JSON data"}, 400

        _logger.info("Paymob Parsed JSON data: %s", pprint.pformat(json_data))

        transaction = json_data.get("transaction")
        intention = json_data.get("intention")
        intention_detail = intention.get("intention_detail", {})
        billing_data = intention_detail.get("billing_data")
        partner_id=int(billing_data.get('first_name').split('+')[0])
        billing_data['first_name']=billing_data.get('first_name').split('+')[1]
        payment_methods = intention.get("payment_methods", [])
        transaction_order_id = transaction.get("order", {}).get("id", [])
        extras=intention.get("extras").get('creation_extras')
        if extras:
            transaction_reference=extras.get('transaction_reference',"S0")
            # t_invoice_id = request.env['account.move'].sudo().search([('name', '=', transaction_reference.split('-')[0])])
            # t_sale_order_id = request.env['sale.order'].sudo().search([('name', '=', transaction_reference.split('-')[0])])
            if transaction_reference:
                t_invoice_id=request.env['account.move'].sudo().search([('name','=',transaction_reference.split('-')[0])])
                t_sale_order_id=request.env['sale.order'].sudo().search([('name','=',transaction_reference.split('-')[0])])
                company_id=t_invoice_id.company_id.id or t_sale_order_id.company_id.id
        if billing_data.get("first_name") == ".":
            name = billing_data.get("last_name")
        else:
            name = billing_data.get("first_name") + " " + billing_data.get("last_name")

        if transaction and transaction.get("success") and not json_data.get("state"):
            if intention and intention_detail and billing_data:
                partner_id = (
                    request.env["res.partner"]
                    .sudo()
                    .search(
                        [("id","=",partner_id),("name", "=", name), ("email", "=", billing_data.get("email"))],
                    )
                )

                payment_transaction_id = (
                    request.env["payment.transaction"]
                    .sudo()
                    .search(
                        [
                            ("partner_id", "=", partner_id[0].id),
                            ("state", "=", "draft"),
                            ("amount", "=", transaction.get("amount_cents") / 100.0),
                        ],
                        limit=1,
                    )
                )

                if not payment_transaction_id:
                    payment_method_list = payment_methods
                    if payment_method_list:
                        for vals in payment_method_list:
                            if vals.get("integration_id"):
                                payment_method_id = request.env[
                                    "payment.method"
                                ].search(
                                    [("integration_id", "=", vals["integration_id"])],
                                    limit=1,
                                )
                                if (
                                        payment_method_id
                                        and payment_method_id.provider_ids[0].sudo().code
                                        == "paymob"
                                ):
                                    currency_id = (
                                        request.env["res.currency"]
                                        .sudo()
                                        .search(
                                            [("name", "=", transaction.get("currency"))]
                                        )
                                    )
                                    bank_type_journal_id = (
                                        request.env["account.journal"]
                                        .sudo()
                                        .search([("type", "=", "bank"), ("company_id", "=", company_id)],
                                                limit=1)
                                    )
                                    payment_id = (
                                        request.env["account.payment"]
                                        .sudo()
                                        .create(
                                            {
                                                "company_id": company_id,
                                                "payment_type": "inbound",
                                                "partner_id": partner_id[0].id,
                                                "amount": transaction.get(
                                                    "amount_cents"
                                                )
                                                          / 100.0,
                                                "currency_id": currency_id.id,
                                                "date": date.today(),
                                                "journal_id": bank_type_journal_id.id,
                                                # "payment_method_selection": "link",
                                            }
                                        )
                                    )
                                    payment_id.action_post()
                                    payment_id.action_validate()

                                    if transaction.get('success') or transaction.get('pending'):
                                        if t_sale_order_id:
                                            if t_sale_order_id.state in ['draft', 'sent']:
                                                t_sale_order_id.action_confirm()

                                    payment_transaction_id = (
                                        request.env["payment.transaction"]
                                        .sudo()
                                        .search(
                                            [('reference', '=', intention.get('extras').get('creation_extras').get(
                                                'transaction_reference'))],
                                            limit=1,
                                        )
                                    )
                                    if payment_transaction_id.invoice_ids:
                                        invoice_id = payment_transaction_id.invoice_ids[0]
                                        # payment_id = self._create_payment(
                                        #     invoice_id,
                                        #     transaction.get("amount_cents") / 100.0,
                                        #     payment_transaction_id,
                                        # )
                                        payment_transaction_id.sudo().write(
                                            {
                                                "state": "done",
                                                "paymob_transaction_id": transaction.get("id"),
                                                "paymob_order_id": transaction_order_id,
                                                # "payment_id": payment_id,
                                                "is_post_processed": False,
                                                # "provider_reference": "paymob-" + payment_transaction_id.invoice_ids[
                                                #     0].name,
                                            }
                                        )
                                        json_data["state"] = True
                                    else:
                                        if payment_transaction_id:
                                            # payment_id = self._create_payment_using_website(
                                            #     t_sale_order_id,
                                            #     transaction.get("amount_cents") / 100.0,
                                            #     payment_transaction_id,
                                            # )
                                            payment_transaction_id.sudo().write(
                                                {
                                                    "state": "done",
                                                    "paymob_transaction_id": transaction.get("id"),
                                                    "paymob_order_id": transaction_order_id,
                                                    # "payment_id": payment_id,
                                                    "is_post_processed": False,
                                                    # "provider_reference": "paymob-" + payment_transaction_id.invoice_ids[
                                                    #     0].name,
                                                }
                                            )
                                            json_data["state"] = True
                else:
                    if (payment_transaction_id.sale_order_ids and not payment_transaction_id.invoice_ids):
                        order_id = payment_transaction_id.sale_order_ids[0]
                        if order_id.state != "sale":
                            order_id.action_confirm()
                        if not order_id.invoice_ids:
                            wizard_id = (
                                request.env["sale.advance.payment.inv"]
                                .with_context(
                                    {
                                        "active_model": "sale.order",
                                        "active_ids": [order_id.id],
                                        "active_id": order_id.id,
                                    }
                                )
                                .sudo()
                                .create(
                                    {
                                        "advance_payment_method": "delivered",
                                    }
                                )
                            )
                            # Create invoices from the wizard
                            invoice_vals = wizard_id.create_invoices()

                            # Fetch the created invoice
                            invoice_id = request.env[
                                invoice_vals.get("res_model")
                            ].browse(invoice_vals.get("res_id"))[0]

                            invoice_id.sudo().write(
                                {
                                    # "payment_method_selection": "link",
                                    "advance_payment": True,
                                    "total_amount_payable": transaction.get(
                                        "amount_cents"
                                    )
                                                            / 100.0,
                                    "balance_due": transaction.get("amount_cents")
                                                   / 100.0,
                                    "amount_payable": abs(
                                        invoice_id.amount_payable
                                    ),
                                }
                            )

                            # Action post to validate the invoice
                            invoice_id.sudo().action_post()
                            # payment_id = self._create_payment(
                            #     invoice_id,
                            #     9 + transaction.get("amount_cents") / 100.0,
                            # )
                            payment_transaction_id.sudo().write(
                                {
                                    "state": "done",
                                    "invoice_ids": [(4, invoice_id.id)],
                                    "paymob_transaction_id": transaction.get("id"),
                                    "paymob_order_id": transaction_order_id,
                                }
                            )
                            json_data["state"] = True
                    else:
                        if payment_transaction_id.invoice_ids:
                            invoice_id = payment_transaction_id.invoice_ids[0]
                            payment_id = self._create_payment(
                                invoice_id,
                                transaction.get("amount_cents") / 100.0,
                                payment_transaction_id,
                            )
                            payment_transaction_id.sudo().write(
                                {
                                    "state": "done",
                                    "paymob_transaction_id": transaction.get("id"),
                                    "paymob_order_id": transaction_order_id,
                                    "payment_id": payment_id,
                                    "is_post_processed":True,
                                    "provider_reference": "paymob-" + payment_transaction_id.invoice_ids[0].name,
                                }
                            )
                            json_data["state"] = True

        else:
            if not transaction.get("success"):
                integration_id = transaction.get("integration_id")
                amount = intention_detail.get("amount")
                request.env["ir.logging"].sudo().create(
                    {
                        "name": "paymob",
                        "type": "server",
                        "level": "INFO",
                        "dbname": request.env.cr.dbname,
                        "message": f"Transaction Failed. Customer Name - {name}, Transaction ID - {integration_id}, Order ID - {transaction_order_id}, Amount - {amount}",
                        "func": "",
                        "path": "",
                        "line": "",
                    }
                )

        event_type = json_data.get("type")
        if event_type == "TOKEN":
            return self._handle_token(json_data)

        elif event_type == "TRANSACTION":
            return self._handle_transaction(json_data)

        else:
            _logger.info("Received paymob callback to flash merchant")

            normalized_data = self._normalize_data(json_data)
            if not normalized_data:
                _logger.error("Paymob: Unexpected callback format")
                return {"error": "Unexpected callback format"}, 400
            _logger.info("Paymob Normalized JSON data")
            return self._handle_transaction(normalized_data)

    def _create_payment(self, invoice, amount, payment_transaction_id):
        bank_journal = (
            request.env["account.journal"].sudo().search(
                [("type", "=", "bank"), ("company_id", "=", invoice.company_id.id)], limit=1)
        )
        payment_register = (
            request.env["account.payment.register"]
            .with_context(
                active_model="account.move.line", active_ids=invoice.line_ids.ids
            )
            .sudo()
            .create(
                {
                    "payment_date": invoice.date,
                    "journal_id": bank_journal.id,
                    "amount": amount,
                    "partner_id": invoice.partner_id.id,
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    # "payment_method_selection": "link",
                }
            )
        )
        payment = payment_register._create_payments()
        payment_method_id = request.env["account.payment.method.line"].sudo().search([('name','=','Paymob')])
        payment.sudo().write({
            "activity_user_id": invoice.invoice_user_id.id,
            "payment_method_line_id":payment_method_id.id,
            "payment_transaction_id":payment_transaction_id.id,
        })
        payment.sudo().action_validate()
        return payment


    def _handle_transaction(self, json_data):
        received_hmac = request.httprequest.args.get("hmac") or json_data.get(
            "obj"
        ).get("hmac")
        hmac_secret = (
            request.env["payment.provider"]
            .sudo()
            .search([("code", "=", "paymob")])
            .paymob_hmac
        )
        calculated_hmac = self._calculate_hmac(hmac_secret, json_data)

        if received_hmac != calculated_hmac:
            _logger.error("HMAC verification failed.")
            return "HMAC verification failed", 400

        # if it's a shopify transaction, search for the transaction based on the email or phone number
        # it's done here not in the _get_tx_from_notification_data method as transaction may not have provider_code yet
        transaction = None
        try:
            if json_data["obj"].get("payment_key_claims")["extra"].get("api_source"):
                if (
                        json_data["obj"]["payment_key_claims"]["extra"]["api_source"]
                        == "SHOPIFY"
                ):
                    # search for the transaction based on the email or phone number

                    # email may be passed as 'NA' in the billing data
                    email = json_data["obj"]["payment_key_claims"]["billing_data"].get(
                        "email"
                    )
                    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if email and re.match(email_regex, email):
                        transaction = (
                            request.env["payment.transaction"]
                            .sudo()
                            .search(
                                [
                                    (
                                        "partner_email",
                                        "=",
                                        json_data["obj"]["payment_key_claims"][
                                            "billing_data"
                                        ]["email"],
                                    ),
                                    # ("provider_code", "=", "paymob"),
                                    (
                                        "amount",
                                        "=",
                                        json_data["obj"]["amount_cents"]
                                        / const.CURRENCIES_DIVISORS.get(
                                            json_data["obj"]["currency"]
                                        ),
                                    ),
                                    # ("create_date", ">=", datetime.now() - timedelta(minutes=15)),
                                ],
                                order="create_date desc",
                                limit=1,
                            )
                        )

                    elif json_data["obj"]["payment_key_claims"]["billing_data"].get(
                            "phone_number"
                    ):
                        transaction = (
                            request.env["payment.transaction"]
                            .sudo()
                            .search(
                                [
                                    (
                                        "partner_phone",
                                        "=",
                                        json_data["obj"]["payment_key_claims"][
                                            "billing_data"
                                        ]["phone_number"],
                                    ),
                                    # ("provider_code", "=", "paymob"),
                                    (
                                        "amount",
                                        "=",
                                        json_data["obj"]["amount_cents"]
                                        / const.CURRENCIES_DIVISORS.get(
                                            json_data["obj"]["currency"]
                                        ),
                                    ),
                                    # ("create_date", ">=", datetime.now() - timedelta(minutes=15)),
                                ],
                                order="create_date desc",
                                limit=1,
                            )
                        )
        except Exception as e:
            _logger.error(
                "Error searching for transaction from shopify callback: %s", e
            )
            pass

        if transaction:
            transaction.provider_code = "paymob"

        else:
            transaction = (
                request.env["payment.transaction"]
                .sudo()
                ._get_tx_from_notification_data("paymob", json_data)
            )

        # not found
        if not transaction:
            _logger.error("Transaction not found.")
            return "Transaction not found", 404

        transaction._handle_notification_data("paymob", json_data)

        return "Transaction processed successfully", 200

    def _handle_token(self, json_data):
        token_data = json_data.get("obj")
        if not token_data:
            _logger.error("No token data found.")
            return {"error": "No token data found"}, 400

        try:
            # Get the payment provider
            paymob_provider = (
                request.env["payment.provider"]
                .sudo()
                .search([("code", "=", "paymob")], limit=1)
            )
            if not paymob_provider:
                _logger.error("Paymob provider not found.")
                return {"error": "Paymob provider not found"}, 404

            base_url = paymob_provider._paymob_get_api_url()

            # Get authentication token
            auth_url = f"{base_url}/api/auth/tokens"
            auth_response = requests.post(
                auth_url, json={"api_key": paymob_provider.paymob_api_key}
            )

            auth_token = auth_response.json().get("token")
            if not auth_token:
                _logger.error("Authentication token not found in response.")
                return {"error": "Token retrieval failed"}, 500

            # Transaction inquiry
            inquiry_url = f"{base_url}/api/ecommerce/orders/transaction_inquiry"
            headers = {"Authorization": f"Bearer {auth_token}"}
            payload = {"order_id": token_data["order_id"]}
            inquiry_response = requests.post(inquiry_url, json=payload, headers=headers)
            if inquiry_response.status_code != 200:
                _logger.error("Transaction inquiry failed.")
                return {"error": "Transaction inquiry failed"}, 500
            inquiry_data = inquiry_response.json()

            try:
                transaction_reference = inquiry_data["payment_key_claims"]["extra"][
                    "transaction_reference"
                ]
            except KeyError:
                return {"error": "Transaction reference not found"}, 404

            # Get payment transaction
            payment_transaction = (
                request.env["payment.transaction"]
                .sudo()
                .search(
                    [
                        ("reference", "=", transaction_reference),
                        ("provider_code", "=", "paymob"),
                    ],
                    limit=1,
                )
            )
            if not payment_transaction:
                _logger.error("Payment transaction not found.")
                return {"error": "Payment transaction not found"}, 404

            payment_method = payment_transaction.payment_method_id.id

            partner = (
                request.env["res.partner"]
                .sudo()
                .search([("email", "=", token_data["email"])], limit=1)
            )
            if not partner:
                _logger.error("Partner not found for email: %s", token_data["email"])
                return {"error": "Partner not found"}, 404

            # Create payment token
            token_values = {
                "provider_id": paymob_provider.id,
                "partner_id": partner.id,
                "payment_method_id": payment_method,
                "payment_details": f"{token_data['card_subtype']} {token_data['masked_pan']}",
                "provider_ref": token_data["id"],
                "paymob_reference": token_data["token"],
                "active": True,
                "create_date": token_data["created_at"],
                "paymob_order_id": token_data["order_id"],
            }

            payment_token = request.env["payment.token"].sudo().create(token_values)
            _logger.info("Payment token created with ID: %s", payment_token.id)

            payment_transaction.write({"token_id": payment_token.id})

            return {"status": "Token processed successfully"}, 200

        except Exception as e:
            _logger.error("Error processing token: %s", e)
            return {"error": f"Error processing token: {str(e)}"}, 500

    def _calculate_hmac(self, key, json_data):
        try:
            data = json_data["obj"].copy()
            data["order"] = data["order"]["id"]

            data["is_3d_secure"] = "true" if data["is_3d_secure"] else "false"
            data["is_auth"] = "true" if data["is_auth"] else "false"
            data["is_capture"] = "true" if data["is_capture"] else "false"
            data["is_refunded"] = "true" if data["is_refunded"] else "false"
            data["is_standalone_payment"] = (
                "true" if data["is_standalone_payment"] else "false"
            )
            data["is_voided"] = "true" if data["is_voided"] else "false"
            data["success"] = "true" if data["success"] else "false"
            data["error_occured"] = "true" if data["error_occured"] else "false"
            data["has_parent_transaction"] = (
                "true" if data["has_parent_transaction"] else "false"
            )
            data["pending"] = "true" if data["pending"] else "false"
            data["source_data_pan"] = data["source_data"]["pan"]
            data["source_data_type"] = data["source_data"]["type"]
            data["source_data_sub_type"] = data["source_data"]["sub_type"]

            concatenated_string = (
                    str(data["amount_cents"])
                    + str(data["created_at"])
                    + str(data["currency"])
                    + str(data["error_occured"])
                    + str(data["has_parent_transaction"])
                    + str(data["id"])
                    + str(data["integration_id"])
                    + str(data["is_3d_secure"])
                    + str(data["is_auth"])
                    + str(data["is_capture"])
                    + str(data["is_refunded"])
                    + str(data["is_standalone_payment"])
                    + str(data["is_voided"])
                    + str(data["order"])
                    + str(data["owner"])
                    + str(data["pending"])
                    + str(data["source_data_pan"])
                    + str(data["source_data_sub_type"])
                    + str(data["source_data_type"])
                    + str(data["success"])
            )
            calculated_hmac = hmac.new(
                key.encode("utf-8"), concatenated_string.encode("utf-8"), hashlib.sha512
            ).hexdigest()

            return calculated_hmac
        except Exception as e:
            _logger.error("Error calculating HMAC: %s", e)
            return None

    def _normalize_data(self, callback_data):
        """
        Normalize the callback data received from Paymob.
        This function is used to convert the callback data to a common format.
        """
        try:
            if (
                    "hmac" in callback_data
                    and "transaction" in callback_data
                    and not callback_data.get("state")
            ):
                normalized_data = {
                    "type": "TRANSACTION",
                    "obj": {
                        "id": callback_data["transaction"]["id"],
                        "hmac": callback_data["hmac"],
                        "pending": callback_data["transaction"]["pending"],
                        "amount_cents": callback_data["transaction"]["amount_cents"],
                        "success": callback_data["transaction"]["success"],
                        "is_auth": callback_data["transaction"]["is_auth"],
                        "is_capture": callback_data["transaction"]["is_capture"],
                        "is_standalone_payment": callback_data["transaction"][
                            "is_standalone_payment"
                        ],
                        "is_void": callback_data["transaction"]["is_voided"],
                        "is_voided": callback_data["transaction"]["is_voided"],
                        "is_refund": callback_data["transaction"]["is_refunded"],
                        "is_refunded": callback_data["transaction"]["is_refunded"],
                        "error_occured": callback_data["transaction"]["error_occured"],
                        "is_3d_secure": callback_data["transaction"]["is_3d_secure"],
                        "integration_id": callback_data["transaction"][
                            "integration_id"
                        ],
                        "has_parent_transaction": callback_data["transaction"][
                            "has_parent_transaction"
                        ],
                        "order": {
                            "id": callback_data["transaction"]["order"]["id"],
                            "amount_cents": callback_data["transaction"][
                                "amount_cents"
                            ],
                            "currency": callback_data["transaction"]["currency"],
                            "items": callback_data["intention"]["intention_detail"].get(
                                "items", []
                            ),
                        },
                        "owner": callback_data["transaction"]["owner"],
                        "created_at": callback_data["transaction"]["created_at"],
                        "currency": callback_data["transaction"]["currency"],
                        "source_data": callback_data["transaction"]["source_data"],
                        "is_captured": callback_data["transaction"]["is_capture"],
                        "captured_amount": callback_data["transaction"].get(
                            "captured_amount", 0
                        ),
                        "payment_key_claims": {
                            "extra": callback_data["intention"]["extras"].get(
                                "creation_extras", {}
                            ),
                        },
                    },
                }
                return normalized_data

            else:
                _logger.error("Paymob: Unexpected callback format")
                return None
        except Exception as e:
            _logger.error("Paymob: Unexpected callback format")
            return None
