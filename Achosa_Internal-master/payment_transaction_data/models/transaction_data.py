from datetime import date
# from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI
from odoo.addons.payment_transaction_data.models.authorize_request import PaymentTransactionDataAuthorizeAPI as AuthorizeAPI
from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    is_audited = fields.Boolean()


class TransactionData(models.Model):
    _name = 'transaction.audit'
    _description = 'Transaction Audit'
    _rec_name = 'record_date'
    # _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    company_id = fields.Many2one('res.company', required=False, default=lambda self: self.env.company)
    acquirer_id = fields.Many2one('payment.acquirer')
    transaction_audit_line_ids = fields.One2many('transaction.audit.line', 'transaction_id')
    unsettled_transaction_ids = fields.One2many('unsettled.transaction.line', 'unsettled_transaction_id')
    record_date = fields.Date(default=fields.Date.context_today)
    report_date = fields.Date(default=fields.Date.today().strftime('%Y-%m-%d'))

    def match_transactions_id(self, days=False):
        # res = [{'transaction_id': '123456', 'date': '2021-11-16'}, {'transaction_id': '42044558829', 'date': '2020-06-05'}]
        payment_authorize = self.env['payment.acquirer'].search([('provider', '=', 'authorize')], limit=1)
        auth_api = AuthorizeAPI(payment_authorize)
        batch_ids = auth_api.get_batch_ids(days)
        unsettled_transactions = auth_api.get_unsettled_transaction_list()
        transaction_list = []
        unsettled_transaction_list = []
        if batch_ids:
            for batch_id in batch_ids:
                res = auth_api.get_transaction_list(batch_id)
                if res:
                    for transaction in res:
                        transactions = self.env['payment.transaction'].search(
                            [('acquirer_reference', '=', transaction['transaction_id'])])
                        if transactions:
                            transactions.is_audited = True
                            continue
                        elif transaction['status'] not in ['voided', 'refundSettledSuccessfully']:
                            trans_id = transaction['transaction_id']
                            specific_transaction = auth_api.get_specific_transaction_details(trans_id)
                            if specific_transaction:
                                msg = 'None'
                                if specific_transaction['card_response'] == "M":
                                    msg = 'CVV matched.'
                                elif specific_transaction['card_response'] == "N":
                                    msg = 'CVV did not match.'
                                elif specific_transaction['card_response'] == "P":
                                    msg = 'CVV was not processed.'
                                elif specific_transaction['card_response'] == "S":
                                    msg = 'CVV should have been present but was not indicated.'
                                elif specific_transaction['card_response'] == "U":
                                    msg = 'The issuer was unable to process the CVV check.'
                                transaction['card_response'] = msg
                                if specific_transaction['cavv_response'] is None:
                                    transaction['cavv_response'] = 'None'
                                else:
                                    transaction['cavv_response'] = specific_transaction['cavv_response']
                            transaction_list.append(transaction)
        if unsettled_transactions:
            for transaction in unsettled_transactions:
                transactions = self.env['payment.transaction'].search(
                    [('acquirer_reference', '=', transaction['transaction_id'])])
                if transactions:
                    transactions.is_audited = True
                    continue
                elif transaction['status'] == 'declined':
                    trans_id = transaction['transaction_id']
                    specific_transaction = auth_api.get_specific_transaction_details(trans_id)
                    if specific_transaction:
                        msg = 'None'
                        if specific_transaction['card_response'] == "M":
                            msg = 'CVV matched.'
                        elif specific_transaction['card_response'] == "N":
                            msg = 'CVV did not match.'
                        elif specific_transaction['card_response'] == "P":
                            msg = 'CVV was not processed.'
                        elif specific_transaction['card_response'] == "S":
                            msg = 'CVV should have been present but was not indicated.'
                        elif specific_transaction['card_response'] == "U":
                            msg = 'The issuer was unable to process the CVV check.'
                        transaction['card_response'] = msg
                        if specific_transaction['cavv_response'] is None:
                            transaction['cavv_response'] = 'None'
                        else:
                            transaction['cavv_response'] = specific_transaction['cavv_response']
                    unsettled_transaction_list.append(transaction)
        var = self.env['transaction.audit'].create({
            'record_date': date.today()
        })
        if transaction_list:
            for transaction in transaction_list:
                var.transaction_audit_line_ids = [(0, 0, {
                    'transaction_no': transaction['transaction_id'],
                    'transaction_date': transaction['date'],
                    'customer_name': transaction['customer_name'],
                    'amount': transaction['amount'],
                    'invoice_no': transaction['invoice'],
                    'status': transaction['status'],
                    'card_response': transaction['card_response'],
                    'cavv_response': transaction['cavv_response'],
                })]
        if unsettled_transaction_list:
            for transaction in unsettled_transaction_list:
                var.unsettled_transaction_ids = [(0, 0, {
                    'unsettled_transaction_no': transaction['transaction_id'],
                    'unsettled_transaction_date': transaction['date'],
                    'customer_name': transaction['customer_name'],
                    'amount': transaction['amount'],
                    'invoice_no': transaction['invoice'],
                    'status': transaction['status'],
                })]

        template_id = self.env.ref('payment_transaction_data.missed_transaction_data').with_context(
            transaction_data=var)
        if template_id and var:
            template_id.send_mail(var.id, force_send=True)


class TransactionAuditLine(models.Model):
    _name = 'transaction.audit.line'
    _description = 'Transaction Audit Line'

    transaction_id = fields.Many2one('transaction.audit')
    transaction_no = fields.Char()
    transaction_date = fields.Date()
    customer_name = fields.Char()
    amount = fields.Float()
    invoice_no = fields.Char()
    status = fields.Char()
    card_response = fields.Char()
    cavv_response = fields.Char()


class UnsettledTransactionLine(models.Model):
    _name = 'unsettled.transaction.line'
    _description = 'Unsettled Transaction Line'

    unsettled_transaction_id = fields.Many2one('transaction.audit')
    unsettled_transaction_no = fields.Char()
    unsettled_transaction_date = fields.Date()
    customer_name = fields.Char()
    amount = fields.Float()
    invoice_no = fields.Char()
    status = fields.Char()
    card_response = fields.Char()
    cavv_response = fields.Char()
