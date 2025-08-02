import io
import requests
import logging
from datetime import datetime, timedelta
from lxml import etree
from xml.etree import ElementTree as ET
from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI


XMLNS = 'AnetApi/xml/v1/schema/AnetApiSchema.xsd'
_logger = logging.getLogger(__name__)

def strip_ns(xml, ns):
    """Strip the provided name from tag names.

    :param str xml: xml document
    :param str ns: namespace to strip

    :rtype: etree._Element
    :return: the parsed xml string with the namespace prefix removed
    """
    it = ET.iterparse(io.BytesIO(xml))
    ns_prefix = '{%s}' % XMLNS
    for _, el in it:
        if el.tag.startswith(ns_prefix):
            el.tag = el.tag[len(ns_prefix):]  # strip all Auth.net namespaces
    return it.root

class PaymentTransactionDataAuthorizeAPI(AuthorizeAPI):

    def _authorize_request(self, data):
        """Encode, send and process the request to the Authorize.net API.

        Encodes the xml data and process the response. Note that only a basic
        processing is done at this level (namespace cleanup, basic error management).

        :param etree._Element data: etree data to process
        """
        data = etree.tostring(data, encoding='utf-8')
        #_logger.log(logging.INFO, '\n'+str(data)+'\n')
        r = requests.post(self.url, data=data, headers={'Content-Type': 'text/xml'})
        r.raise_for_status()
        response = strip_ns(r.content, XMLNS)
        return response

    def _base_tree(self, requestType):
        """Create a basic tree containing authentication information.

        Create a etree Element of type requestType and appends the Authorize.net
        credentials (they are always required).
        :param str requestType: the type of request to send to Authorize.net
                                See http://developer.authorize.net/api/reference
                                for available types.
        :return: basic etree Element of the requested type
                               containing credentials information
        :rtype: etree._Element
        """
        root = etree.Element(requestType, xmlns=XMLNS)
        auth = etree.SubElement(root, "merchantAuthentication")
        etree.SubElement(auth, "name").text = self.name
        etree.SubElement(auth, "transactionKey").text = self.transaction_key
        return root

    def get_batch_ids(self, days=30):
        batches = []
        date_from = (datetime.now() - timedelta(days)).strftime('%Y-%m-%dT00:00:00')
        date_to = datetime.now().strftime('%Y-%m-%dT23:59:59')

        root = self._base_tree('getSettledBatchListRequest')
        etree.SubElement(root, "firstSettlementDate").text = date_from
        etree.SubElement(root, "lastSettlementDate").text = date_to
        response = self._authorize_request(root)

        msg = response.find('messages')
        batchlist = response.find('batchList')
        if msg is not None:
            rc = msg.find('resultCode')
            if rc is not None:
                err = msg.find('message')
                # err_code = err.find('code').text
                err_msg = err.find('text').text
                _logger.info('Batch message: %s' % err_msg)
                if err_msg == 'Successful.' and batchlist is not None:
                    for rec in batchlist:
                        batch_id = rec.find('batchId').text
                        batches.append(batch_id)
        return batches

    def get_transaction_list(self, batch_id=""):
        if batch_id is None:
            return []
        transaction_ids = []

        root = self._base_tree('getTransactionListRequest')
        etree.SubElement(root, "batchId").text = batch_id
        response = self._authorize_request(root)

        msg = response.find('messages')
        transactions = response.find('transactions')
        if msg is not None:
            rc = msg.find('resultCode')
            if rc is not None:
                err = msg.find('message')
                # err_code = err.find('code').text
                err_msg = err.find('text').text
                _logger.info('Settled transaction message: %s' % err_msg)
                if err_msg == 'Successful.' and transactions is not None:
                    for rec in transactions:
                        if rec.find('firstName') is not None:
                            first_name = rec.find('firstName').text
                        else:
                            first_name = ''
                        if rec.find('lastName') is not None:
                            last_name = rec.find('lastName').text
                        else:
                            last_name = ''
                        if rec.find('invoiceNumber') is not None:
                            invoice = rec.find('invoiceNumber').text
                        else:
                            invoice = 'None'
                        single_transaction = {
                            'transaction_id': rec.find('transId').text,
                            'date': rec.find('submitTimeUTC').text,
                            'customer_name': first_name + ' ' + last_name,
                            'amount': rec.find('settleAmount').text,
                            'invoice': invoice,
                            'status': rec.find('transactionStatus').text,
                            'card_response': '',
                            'cavv_response': '',
                        }
                        transaction_ids.append(single_transaction)
        return transaction_ids

    def get_unsettled_transaction_list(self):
        root = self._base_tree('getUnsettledTransactionListRequest')
        response = self._authorize_request(root)
        unsettled_transaction_ids = []

        msg = response.find('messages')
        transactions = response.find('transactions')
        if msg is not None:
            rc = msg.find('resultCode')
            if rc is not None:
                err = msg.find('message')
                # err_code = err.find('code').text
                err_msg = err.find('text').text
                _logger.info('Unsettled transaction message: %s' % err_msg)
                if err_msg == 'Successful.' and transactions is not None:
                    for rec in transactions:
                        if rec.find('firstName') is not None:
                            first_name = rec.find('firstName').text
                        else:
                            first_name = ''
                        if rec.find('lastName') is not None:
                            last_name = rec.find('lastName').text
                        else:
                            last_name = ''
                        if rec.find('invoiceNumber') is not None:
                            invoice = rec.find('invoiceNumber').text
                        else:
                            invoice = ''
                        transaction = {
                            'transaction_id': rec.find('transId').text,
                            'date': rec.find('submitTimeUTC').text,
                            'customer_name': first_name + ' ' + last_name,
                            'amount': rec.find('settleAmount').text,
                            'invoice': invoice,
                            'status': rec.find('transactionStatus').text,
                            'card_response': '',
                            'cavv_response': '',
                        }
                        unsettled_transaction_ids.append(transaction)
        return unsettled_transaction_ids

    def get_specific_transaction_details(self, trans_id=""):
        if trans_id is None:
            return []

        root = self._base_tree('getTransactionDetailsRequest')
        etree.SubElement(root, "transId").text = trans_id
        response = self._authorize_request(root)
        specific_transaction_ids = []

        msg = response.find('messages')
        transactions = response.find('transaction')
        # _logger.info('Specific transaction object message %s' % response.find('getTransactionDetailsResponse').find('transaction').find('CAVVResponse').text)
        if msg is not None:
            rc = msg.find('resultCode')
            if rc is not None:
                err = msg.find('message')
                # err_code = err.find('code').text
                err_msg = err.find('text').text
                _logger.info('Specific transaction message %s' % err_msg)
                if err_msg == 'Successful.' and transactions is not None:
                    if transactions.find('CAVVResponse') is not None:
                        cavv_number = transactions.find('CAVVResponse').text
                    else:
                        cavv_number = None
                    transaction = {
                        'card_response': transactions.find('cardCodeResponse').text,
                        'cavv_response': cavv_number
                    }
                    # specific_transaction_ids.append(transaction)
                    return transaction
