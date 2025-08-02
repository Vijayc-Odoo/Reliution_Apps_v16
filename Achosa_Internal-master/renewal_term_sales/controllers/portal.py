# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import http
from odoo.addons.sale.controllers.portal import CustomerPortal

_LOGGER = logging.getLogger("##### Renewal Term Sales #####")


class RenewalCustomerPortal(CustomerPortal):

    @http.route([
        '/my/orders/<int:order_id>',
    ], type='http', auth='public', website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        response = super(RenewalCustomerPortal, self).portal_order_page(order_id=order_id, report_type=report_type,
                                                                        access_token=access_token, message=message,
                                                                        download=download, **kw)
        if not 'sale_order' in response.qcontext:
            return response
        order = response.qcontext['sale_order']
        renewal_error_message = ""
        if order.state in ('draft', 'sent') and kw.get('renewal_term', False):
            renewal_order_lines_status = order.update_renewal_order_lines(**kw)
            if renewal_order_lines_status and isinstance(renewal_order_lines_status, list):
                renewal_error_message = f"Please contact your sales person for {kw.get('renewal_term', '')} " \
                                        f"Renewal."
                _LOGGER.info(f"Renewal Error Message: {renewal_error_message}")
        # AO-1004 NOOP Renewal Fix
        elif order.state in ('draft', 'sent'):
            order.set_owner_renewal_product()

        # AO-996: Yearly/Monthly Toggle Issue on Sales Orders
        # response = super(RenewalCustomerPortal, self).portal_order_page(order_id=order_id, report_type=report_type,
        #                                                                 access_token=access_token, message=message,
        #                                                                 download=download, **kw)
        response.qcontext.update({
            'renewal_error_message': renewal_error_message,
        })
        return response

