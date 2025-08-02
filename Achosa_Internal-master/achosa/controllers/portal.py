# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.exceptions import AccessError
from odoo.http import request
from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import NotFound
from datetime import datetime
import json
from odoo.tools import html_escape as escape

import logging, re

_logger = logging.getLogger("##### Achosa #####")


class PortalHomeWarranty(CustomerPortal):

    draft_required = [
                    'property_street',
                    'property_city',
                    'property_state',
                    'property_zip',
                    'property_type'
                ]
    seller_required = [
                'seller_name',
                'covered_seller_product_id',
                'coverage_start_date'
    ]
    buyer_required = [
                'buyer_name',
                'covered_buyer_product_id',
                'covered_buyer_term',
    ]

    def _prepare_portal_layout_values(self):
        """
        Gets counts of document types in portal landing page
        :return:
        """
        values = super(PortalHomeWarranty, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        domain = [('realtor_contact','=',partner.id)]
        if partner.parent_id and partner.vendor_type and partner.vendor_type == 'Coordinator':
            domain = [('realtor_contact.parent_id','=',partner.parent_id.id)]
        home_warranty_count = request.env['home.warranty'].sudo().search_count(domain)
        values['home_warranty_count'] = home_warranty_count
        return values

    @http.route(['/my/home_warranties', '/my/home_warranties/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_home_warranties(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """
        Portal list of home warranty orders
        :param page: current page - not used
        :param date_begin: filter by date - not used
        :param date_end: filter by date - not used
        :param sortby: sort by field - not used
        :param kw: not used
        :return: rendered page
        """
        partner = request.env.user.partner_id
        HomeWarrranty = request.env['home.warranty']
        domain = [('realtor_contact','=',partner.id)]
        if partner.parent_id and partner.vendor_type and partner.vendor_type == 'Coordinator':
            domain = [('realtor_contact.parent_id','=',partner.parent_id.id)]
        home_warranties = HomeWarrranty.sudo().search(domain)

        return request.render("achosa.portal_my_home_warranty", {"home_warranties": home_warranties})

    @staticmethod
    def validate_covered_buyer_addons(data,browse=False):
        if 'covered_buyer_addons' in data and data['covered_buyer_addons']:
            covered_buyer_addons = str(data['covered_buyer_addons']).replace('[', '').replace(']', '')
            if len(covered_buyer_addons) > 1:
                covered_buyer_addons = list(set(covered_buyer_addons.split(',')))
                data['covered_buyer_addons'] = covered_buyer_addons
                for a in range(len(covered_buyer_addons)):
                    data['covered_buyer_addons'][a] = int(covered_buyer_addons[a])
                if browse:
                    data['covered_buyer_addons'] = \
                        request.env['product.attribute.value'].browse(data['covered_buyer_addons'])
            else:
                data['covered_buyer_addons'] = False
        if 'covered_buyer_addons[]' in data:
            del data['covered_buyer_addons[]']
        return data

    def update_data(self):
        """
        Validate posted data against home warranty fields
        :return:
        """
        model_record = request.env['ir.model'].sudo().search(
            [('model', '=', 'home.warranty'), ('website_form_access', '=', True)])
        authorized_fields = ['realtor_contact',
                'realtor_name',
                'realtor_email',
                'realtor_phone',
                'property_street',
                'property_street2',
                'property_city',
                'property_state',
                'property_zip',
                'property_type',
                'name',
                'realtor_representing_buyer',
                'realtor_representing_seller',
                'covered_seller_product_id',
                'covered_sellers_coverage',
                'coverage_start_date',
                'seller_email',
                'seller_name',
                'seller_phone',
                'buyer_email',
                'buyer_name',
                'buyer_phone',
                'covered_buyer_product_id',
                'covered_buyers_coverage',
                'covered_buyer_term',
                'covered_buyer_addons',
                'closing_email',
                'closing_name',
                'estimated_closing_date',
                'promo_code',
                'paying_as']
        data = {}
        error = dict()
        error_message = []
        for field_name, field_value in request.params.items():
            if field_name in authorized_fields:
                if field_value == '':
                    # Check if required for draft
                    if field_name in self.draft_required:
                        error['home.warranty.'+field_name+':'] = "required"
                        error_message.append(field_name + " is required")
                    # check if covered_sellers_coverage checked and required for seller order
                    elif data.get('covered_sellers_coverage') and field_name in self.seller_required:
                        error['home.warranty.'+field_name+':'] = "required"
                        error_message.append(field_name + " is required")
                    # check if covered_buyers_coverage checked and required for buyer order
                    elif data.get('covered_buyers_coverage') and field_name in self.buyer_required:
                        error['home.warranty.'+field_name+':'] = "required"
                        error_message.append(field_name + " is required")
                    data[field_name] = False
                else:
                    # Set Term for New Construction
                    # if field_name == 'property_type' and field_value == 'New':
                    #     data['covered_buyer_term'] = '48'
                    if field_name in ['covered_seller_product_id','covered_buyer_product_id']:
                        data[field_name] = request.env['product.attribute.value'].browse(int(field_value))
                    elif field_name in ['property_state','realtor_contact']:
                        data[field_name] = int(field_value)
                    else:
                        data[field_name] = field_value
        data = self.validate_covered_buyer_addons(data,True)
        # check if covered_sellers_coverage or covered_buyers_coverage checked
        if not data.get('covered_sellers_coverage') and not data.get('covered_buyers_coverage'):
            error['home.warranty.covered_sellers_coverage:'] = "required"
            error['home.warranty.covered_buyers_coverage:'] = "required"
            error_message.append("'Seller and Buyer' or 'Buyers only' coverage is required")


        return data, error, error_message

    @http.route(['/my/home_warranties/<int:home_warranty_id>'], type='http', auth="user", website=True)
    def portal_my_home_warranty_detail(self, home_warranty_id, **post):
        """
        display / update home warranty
        :param home_warranty_id: id of home warranty
        :param post: data to update
        :return: rendered home warranty page
        """
        partner = request.env.user.partner_id
        HomeWarrranty = request.env['home.warranty']
        domain = [('id','=',home_warranty_id),('realtor_contact','=',partner.id)]
        if partner.parent_id and partner.vendor_type and partner.vendor_type == 'Coordinator':
            domain = [('id','=',home_warranty_id),('realtor_contact.parent_id','=',partner.parent_id.id)]
        home_warranty = HomeWarrranty.sudo().search(domain)
        error = dict()
        error_message = []
        if post:
            sales_id = 1
            if request.env.user.user_id.id:
                sales_id = request.env.user.user_id.id
            partner_id = request.env.user.partner_id.id
            user_id = request.env.user.id
            if "noupdate" in post:
                error_message = home_warranty.check_ready_for_subscription(sales_id, partner_id, user_id)
            else:
                data, error, error_message = self.update_data()
                if not error:
                    try:
                        home_warranty.sudo().update(data)
                    except ValueError as e:
                        try:
                            error[str(e).split(' ')[3]] = str(e).split("'")[1]
                        except ValueError:
                            error_message.append("Unable to Save")
                        error_message.append(str(e))
                    if not error:
                        error_message = home_warranty.check_ready_for_subscription(sales_id, partner_id, user_id)
        sales_id = 1
        if request.env.user.user_id.id:
            sales_id = request.env.user.user_id.id
        partner_id = request.env.user.partner_id.id
        user_id = request.env.user.id
        home_warranty.check_ready_for_subscription(sales_id, partner_id, user_id)
        product_ids = home_warranty[0].product.with_context({"pricelist": home_warranty.pricelist_id.id})
        if len(error_message) > 0 and error_message[0].endswith("Applied") and home_warranty.promo:
            total = 0
            for product in product_ids:
                total += product.price
            return request.render("achosa.portal_home_warranty_valid_promo", {
                    'page_name': 'Home Warranty Order',
                    'products': product_ids,
                    'total': total,
                    'home_warranty': home_warranty,
                    'success_message': error_message,
                    'action': '/my/home_warranties/%s' % home_warranty.id
            })
        else:
            states = request.env['res.country.state'].search([['enable_home_warranty', '=', True]])
            domain = ['|', ['id', '=', request.env.user.partner_id.id],
                                                          ['vendor_type', '=', 'Realtor'], ['active', '=', True],
                                                          ['parent_id', '=', request.env.user.partner_id.parent_id.id],
                                                          ]
            if not request.env.user.partner_id.parent_id:
                domain = [['id', '=', request.env.user.partner_id.id]]
            elif request.env.user.partner_id.parent_id.email == 'info@achosahw.com':
                domain = [['vendor_type', '=', 'Realtor'], ['active', '=', True]]
            realtors = request.env['res.partner'].search(domain)
            addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn')])
            return request.render("achosa.portal_home_warranty_page", {
                'states': states,
                'realtors': realtors,
                'page_name': 'Home Warranty Order',
                'home_warranty': home_warranty,
                'add_ons': addons,
                'error': error,
                'error_message': error_message
            })

    @http.route(['/my/home_warranties/<int:home_warranty_id>/products'], type='http', auth="user", website=True)
    def portal_my_home_warranty_products_id(self, home_warranty_id, **kw):
        """
        List products for home warranty - Ajax
        :param home_warranty_id: home warranty id
        :param kw: not used
        :return: rendered products list html
        """
        
        partner = request.env.user.partner_id
        HomeWarrranty = request.env['home.warranty']
        domain = [('id','=',home_warranty_id),('realtor_contact','=',partner.id)]
        if partner.parent_id and partner.vendor_type and partner.vendor_type == 'Coordinator':
            domain = [('id','=',home_warranty_id),('realtor_contact.parent_id','=',partner.parent_id.id)]
        home_warranty = HomeWarrranty.sudo().search(domain)
        total = 0
        
        _logger.log(logging.INFO, str(home_warranty) +'\n'+ home_warranty.state)
        product_ids = home_warranty[0].product.with_context({"pricelist": home_warranty.pricelist_id.id})
        if home_warranty.state in ['Buyer','Owner']:
            for product in product_ids:
                total += product.price
            return request.render("achosa.portal_home_warranty_products", {
                'products': product_ids,
                'total': total
            })
        
        kw['coverage_start_date'] = False
        kw['estimated_closing_date'] = False
        if 'covered_seller_product_id' in kw and len(kw['covered_seller_product_id']):
            kw['covered_seller_product_id'] = int(kw['covered_seller_product_id'])
        if 'covered_buyer_product_id' in kw and len(kw['covered_buyer_product_id']):
            kw['covered_buyer_product_id'] = int(kw['covered_buyer_product_id'])
        # if kw['property_type'] == 'New':
        #     kw['covered_buyer_term'] = '48'
        kw.pop('conserve_plus_add_on_id', None)
        kw.pop('conserve_add_on_id', None)
        kw.pop('non_owner_product_add_on_id', None)
        kw = self.validate_covered_buyer_addons(kw)
        home_warranty_c = request.env['home.warranty'].sudo().new(kw)
        total = 0
        _logger.log(logging.INFO, '/products\n'+str(kw)+'\n'+str(home_warranty_c))

        pricelist_obj = request.env['product.pricelist']
        res_country_state_obj = request.env['res.country.state']
        property_state_id = False
        if home_warranty_c.property_state and home_warranty_c.property_state.id:
            property_state_id = res_country_state_obj.browse(int(home_warranty_c.property_state.id))
        pricelist_id = pricelist_obj.get_home_warranty_pricelist_by_state_wise(property_state_id)
        products = home_warranty_c[0].product._origin.with_context({"pricelist": pricelist_id})
        for product in products:
            total += product.price
        
        if home_warranty.promo:
            products += home_warranty.promo.discount_line_product_id
            total += home_warranty.promo.discount_line_product_id.lst_price

        price_script = home_warranty_c.price_script
        
        return request.render("achosa.portal_home_warranty_products", {
            'products': products,
            'total': total,
            'prices': price_script
        })
    
    
    @http.route(['/my/home_warranties/<int:quotation_id>/update_address'], type='http', auth="public", website=True)
    def update_address(self, quotation_id, **kw):
        """
        Update Billing Address - Ajax
        :param quotation_id: Quotation id
        :param kw: address data data
        :return: rendered status message
        """
        
        if quotation_id == 0:
            invoice_contact = False
            contact = request.env['res.partner'].search([('id','in',request.env.user.partner_id.child_ids.ids), ('type','=','invoice')], limit=1, order="write_date desc")
            if contact:
                invoice_contact = contact
            else:
                contact = request.env['res.partner']
                if 'name' in kw and len(kw['name']):
                    contact_record = contact.sudo().create({
                        "name": kw['name'],
                        "temporary": True
                    })
                    contact_record.parent_id = request.env.user.partner_id
                    contact_record.type = "invoice"
                    invoice_contact = contact_record
                else:
                    return "failure, no name listed"

            if 'name' in kw and len(kw['name']):
                invoice_contact.name = kw['name']
            if 'street' in kw and len(kw['street']):
                invoice_contact.street = kw['street']
            if 'street2' in kw and len(kw['street2']):
                invoice_contact.street2 = kw['street2']
            if 'city' in kw and len(kw['city']):
                invoice_contact.city = kw['city']
            if 'state' in kw and len(kw['state']):
                invoice_contact.state_id = int(kw['state'])
            if 'zip' in kw and len(kw['zip']):
                invoice_contact.zip = kw['zip']    
                
        else:
            SaleOrder = request.env['sale.order']
            domain = [('id','=',quotation_id)]
            sale_order = SaleOrder.sudo().search(domain)
        
            if sale_order.partner_id.type != 'invoice' and sale_order.order_type in ['Buyer', 'Owner']:
                contact = request.env['res.partner']
                if 'name' in kw and len(kw['name']):
                    contact_record = contact.sudo().create({
                        "name": kw['name'],
                        "home_warranty": sale_order.home_warranty.id,
                        "temporary": True
                    })
                    contact_record.parent_id = sale_order.partner_id
                    contact_record.type = "invoice"
                    sale_order.partner_id = contact_record
                else:
                    return "failure, no name listed"
            if 'name' in kw and len(kw['name']):
                sale_order.partner_id.name = kw['name']
            if 'street' in kw and len(kw['street']):
                sale_order.partner_id.street = kw['street']
            if 'street2' in kw and len(kw['street2']):
                sale_order.partner_id.street2 = kw['street2']
            if 'city' in kw and len(kw['city']):
                sale_order.partner_id.city = kw['city']
            if 'state' in kw and len(kw['state']):
                sale_order.partner_id.state_id = int(kw['state'])
            if 'zip' in kw and len(kw['zip']):
                sale_order.partner_id.zip = kw['zip']
        
        return "success"
    
    @http.route(['/my/home_warranties/<int:quotation_id>/retrieve_address'], type='http', auth="public", website=True)
    def retrieve_address(self, quotation_id, **kw):
        """
        Retrieve Address Data - Ajax
        :return: Adress Data
        """
        if quotation_id == 0:
            contact = request.env['res.partner'].search([('id','in',request.env.user.partner_id.child_ids.ids), ('type','=','invoice')], limit=1, order="write_date desc")
            if contact:
                name = contact.name
                street = contact.street
                street2 = contact.street2
                city = contact.city
                state_id = contact.state_id
                zip_code = contact.zip
            else:
                name = None
                street = None
                street2 = None
                city = None
                state_id = None
                zip_code = None
        else:
            SaleOrder = request.env['sale.order']
            domain = [('id','=',quotation_id)]
            sale_order = SaleOrder.sudo().search(domain)
            name = sale_order.partner_id.name
            street = sale_order.partner_id.street
            street2 = sale_order.partner_id.street2
            city = sale_order.partner_id.city
            state_id = sale_order.partner_id.state_id
            zip_code = sale_order.partner_id.zip
        
        states = request.env['res.country.state'].sudo().search([['enable_home_warranty', '=', True]])

        return request.render("achosa.billing_address", {
                "states": states,
                "name": name,
                "street": street,
                "street2": street2,
                "city": city,
                "state_id": state_id,
                "zip_code": zip_code
            })

    @http.route(['/my/home_warranties/<int:home_warranty_id>/messages'], type='http', auth="user", website=True)
    def portal_my_home_warranty_messages(self, home_warranty_id, **kw):
        """
        List Home Warranty Messages - Ajax
        :param home_warranty_id: home warranty id
        :param kw: home warranty data
        :return: rendered messages
        """
        partner = request.env.user.partner_id
        HomeWarrranty = request.env['home.warranty']
        domain = [('id','=',home_warranty_id),('realtor_contact','=',partner.id)]
        if partner.parent_id and partner.vendor_type and partner.vendor_type == 'Coordinator':
            domain = [('id','=',home_warranty_id),('realtor_contact.parent_id','=',partner.parent_id.id)]
        home_warranty = HomeWarrranty.sudo().search(domain)
        messages = []
        if home_warranty[0].id:
            messages = request.env['mail.message'].sudo().search([['model','=','home.warranty'],
                                                        ['res_id','=',home_warranty[0].id],
                                                        ['message_type','=','comment'],
                                                        ['website_published','=',True]
                                                        ]).sorted(key=lambda r: r.date, reverse=True)
        if len(messages) > 0:
            return request.render("achosa.portal_home_warranty_messages", {
                'messages': messages
            })
        else:
            return "<br/>"

    @http.route(['/my/home_warranties/<int:home_warranty_id>/send_Invoice/<string:template_name>'], type='http', auth="user", website=True)
    def portal_my_home_warranty_send_invoice(self, home_warranty_id, template_name='', **kw):
        """
        Send Invoice Action (Ajax button)
        :param home_warranty_id: home warranty id
        :param template_name: template to send including contact type
        :param kw: not used
        :return: rendered html of status
        """
        partner = request.env.user.partner_id
        home_warranty_obj = request.env['home.warranty']
        domain = [('id','=',home_warranty_id),('realtor_contact','=',partner.id)]
        if partner.parent_id and partner.vendor_type and partner.vendor_type == 'Coordinator':
            domain = [('id','=',home_warranty_id),('realtor_contact.parent_id','=',partner.parent_id.id)]
        home_warranty = home_warranty_obj.sudo().search(domain)
        if home_warranty[0].id:
            home_warranty[0].send_invoice('achosa.'+template_name, True, partner.id)
            return "<i class='fa fa-check mr4'></i>The invoice has been sent."
        return "<i class='fa fa-close mr4'></i> An error has occurred, the message has not been sent"

    @http.route(['/my/home_warranties/products'], type='http', auth="user", methods=['POST'], website=True)
    def portal_my_home_warranty_products(self, **kw):
        """
        List products for home warranty data - Ajax Post
        :param kw: home warranty data
        :return: rendered products list html
        """
        kw['coverage_start_date'] = False
        kw['estimated_closing_date'] = False
        if 'covered_seller_product_id' in kw and len(kw['covered_seller_product_id']):
            kw['covered_seller_product_id'] = int(kw['covered_seller_product_id'])
        if 'covered_buyer_product_id' in kw and len(kw['covered_buyer_product_id']):
            kw['covered_buyer_product_id'] = int(kw['covered_buyer_product_id'])
        # if kw['property_type'] == 'New':
        #     kw['covered_buyer_term'] = '48'
        kw.pop('conserve_plus_add_on_id', None)
        kw.pop('conserve_add_on_id', None)
        kw.pop('non_owner_product_add_on_id', None)
        kw = self.validate_covered_buyer_addons(kw)
        home_warranty = request.env['home.warranty'].sudo().new(kw)
        total = 0
        pricelist_obj = request.env['product.pricelist']
        res_country_state_obj = request.env['res.country.state']
        property_state_id = False
        if home_warranty.property_state and home_warranty.property_state.id:
            property_state_id = res_country_state_obj.browse(int(home_warranty.property_state.id))
        pricelist_id = pricelist_obj.get_home_warranty_pricelist_by_state_wise(property_state_id)
        products = home_warranty[0].product._origin.with_context({"pricelist": pricelist_id})
        for product in products:
            total += product.price

        price_script = home_warranty.price_script

        _logger.info(f"HW State : {home_warranty.property_state.id}, Pricelist : {pricelist_id}")
        if home_warranty.property_state.id:
            return request.render("achosa.portal_home_warranty_products", {
                'products': products,
                'total': total,
                'prices': price_script
            })



    @http.route(['/my/home_warranties/addons'], type='http', auth="user", methods=['POST'], csrf=False, website=True)
    def portal_my_home_warranty_add_ons(self, **kw):
        """
        List products for home warranty data - Ajax Post
        :param kw: home warranty data
        :return: rendered products list html
        """
        if 'csrf_token' in kw:
            del kw['csrf_token']
        kw['coverage_start_date'] = False
        kw['estimated_closing_date'] = False
        # if 'property_type' in kw and kw['property_type'] == 'New':
        #     kw['covered_buyer_term'] = '48'
        kw.pop('conserve_plus_add_on_id', None)
        kw.pop('conserve_add_on_id', None)
        kw.pop('non_owner_product_add_on_id', None)
        kw = self.validate_covered_buyer_addons(kw,True)
        home_warranty = request.env['home.warranty'].sudo().new(kw)
        addons = False
        _logger.log(logging.INFO, str(kw))
        rental_addon_id = request.env['home.warranty'].sudo()._get_add_on_noop_attribute_value_id()
        if 'property_state' in kw and len(kw['property_state']) > 0:
            if 'property_type' in kw and (kw['property_type'] in ['Single Family Home','Townhome/Condo','New']):
                addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn'),
                                                                        ('states.id','=',kw['property_state']),
                                                                        '!', ('id','=',227)])
            else:
                addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn'),
                                                                        ('states.id','=',kw['property_state']),
                                                                        '!', ('id','=',rental_addon_id)])
                

        return request.render("achosa.HW_add-ons", {
            'home_warranty': home_warranty[0],
            'add_ons': addons,
            'pricescript': False
        })

    @http.route(['/my/home_warranties/seller_dropdown'], type='http', auth="user",methods=['POST'], csrf=False, website=True)
    def portal_my_home_warranty_seller_dropdown(self, **kw):
        """
        List products for home warranty - Ajax
        :param home_warranty_id: home warranty id
        :param kw: not used
        :return: rendered products list html
        """
        partner = request.env.user.partner_id
        value = ''
        products = False
        if 'covered_seller_product_id' in kw and len(kw['covered_seller_product_id']):
            value = int(kw['covered_seller_product_id'])
        kw = self.validate_covered_buyer_addons(kw)
        state = ''
        if kw.get('id', ''):
            HomeWarrranty = request.env['home.warranty']
            domain = [('id','=',kw['id']),('realtor_contact','=',partner.id)]
            if partner.parent_id and partner.vendor_type and partner.vendor_type == 'Coordinator':
                domain = [('id','=',kw['id']),('realtor_contact.parent_id','=',partner.parent_id.id)]
            home_warranty = HomeWarrranty.sudo().search(domain)
            state = home_warranty[0]['state']
        if state in ['Seller','Buyer','Owner']:
            products = home_warranty[0].covered_seller_product_id
        else:
            property_state = ''
            if 'property_state' in kw and len(kw['property_state']) > 0:
                property_state = kw['property_state']
                products = request.env['product.attribute.value'].sudo()\
                    .search([('states.id','=',property_state), ('term_product_type','=','Seller')])
        if not products or len(products.ids) < 1:
            return "Please Select a state"
        else:
            return request.render("achosa.home_warranty_dropdown", {
                'products': products,
                'field': 'covered_seller_product_id',
                'field_value': value,
                'disable': state in ['Seller','Buyer','Owner']
            })

    @http.route(['/my/home_warranties/buyer_dropdown'], type='http', auth="user",methods=['POST'], csrf=False,  website=True)
    def portal_my_home_warranty_buyer_dropdown(self, **kw):
        """
        List products for home warranty - Ajax
        :param home_warranty_id: home warranty id
        :param kw: not used
        :return: rendered products list html
        """
        partner = request.env.user.partner_id
        value = ''
        products = False
        if 'covered_buyer_product_id' in kw and len(kw['covered_buyer_product_id']):
            value = int(kw['covered_buyer_product_id'])
        kw = self.validate_covered_buyer_addons(kw)
        state = ''
        if kw.get('id', ''):
            HomeWarrranty = request.env['home.warranty']
            domain = [('id','=',kw['id']),('realtor_contact','=',partner.id)]
            if partner.parent_id and partner.vendor_type and partner.vendor_type == 'Coordinator':
                domain = [('id','=',kw['id']),('realtor_contact.parent_id','=',partner.parent_id.id)]
            home_warranty = HomeWarrranty.sudo().search(domain)
            state = home_warranty[0]['state']

        if state in ['Buyer', 'Owner']:
            products = home_warranty[0].covered_buyer_product_id
        else:
            property_state = ''
            if 'property_state' in kw and len(kw['property_state']) > 0:
                property_state = kw['property_state']
                products = request.env['product.attribute.value'].sudo()\
                    .search([('states.id','=',property_state), ('term_product_type','=','Buyer')])
        if not products or len(products.ids) < 1:
            return "Please Select a state"
        else:
            return request.render("achosa.home_warranty_dropdown", {
                'products': products,
                'field': 'covered_buyer_product_id',
                'field_value': value,
                'disable': state in ['Buyer','Owner']
            })

    @http.route('/home_warranty/New', type='http', auth="user", methods=['GET'], website=True)
    def website_home_warranty_form(self, **kwargs):
        """
        Empty home warranty form
        :param kwargs: not used
        :return: rendered home warranty form
        """
        home_warranty = request.env['home.warranty'].sudo().new()
        default_values = {}
        if request.env.user.partner_id != request.env.ref('base.public_partner'):
            default_values['name'] = request.env.user.partner_id.name
            default_values['email'] = request.env.user.partner_id.email
            default_values['realtor'] = request.env.user.partner_id.id
        states = request.env['res.country.state'].search([['enable_home_warranty','=',True]])
        domain = ['|', ['id', '=', request.env.user.partner_id.id],
                                                      ['vendor_type', '=', 'Realtor'], ['active', '=', True],
                                                      ['parent_id', '=', request.env.user.partner_id.parent_id.id],
                                                      ]
        if not request.env.user.partner_id.parent_id:
            domain = [['id', '=', request.env.user.partner_id.id]]
            home_warranty['realtor_contact'] = request.env.user.partner_id.id
        elif request.env.user.partner_id.parent_id.email == 'info@achosahw.com':
            domain = [['vendor_type', '=', 'Realtor'], ['active', '=', True]]
        else:
            home_warranty['realtor_contact'] = request.env.user.partner_id.id
        realtors = request.env['res.partner'].search(domain)
        # products = request.env['product.products'].search(["sale_ok","=","True"])

        addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn')])
        conserve_id, conserve_plus_id = request.env['home.warranty'].sudo()._get_add_on_attribute_value_id()
        rental_addon_id = request.env['home.warranty'].sudo()._get_add_on_noop_attribute_value_id()
        return request.render("achosa.New", {
            'default_values': default_values,
            'home_warranty': home_warranty,
            'add_ons': addons,
            'error': dict(),
            'error_message': [],
            'states': states,
            'realtors': realtors,
            'conserve_id': conserve_id,
            'conserve_plus_id': conserve_plus_id,
            'rental_addon_id': rental_addon_id
        })

    @http.route('/home_warranty/New', type='http', auth="user", methods=['POST'], website=True)
    def website_form(self, **kwargs):
        """
        create new home warranty
        :param kwargs: data for home warranty
        :return: rendered home warranty or status page
        """
        home_warranty = False
        data, error, error_message = self.update_data()
        if 'realtor_contact' in data:
            data['realtor_contact'] = int(data['realtor_contact'])
        if 'covered_buyer_addons' in data and data['covered_buyer_addons'] == False:
            data['covered_buyer_addons'] = []
        if 'covered_buyer_product_id' in data:
            data['covered_buyer_product_id'] = int(data['covered_buyer_product_id'])
        if 'covered_seller_product_id' in data:
            data['covered_seller_product_id'] = int(data['covered_seller_product_id'])
        if 'covered_buyers_coverage' in data:
            if data['covered_buyers_coverage'] == 'on':
                data['covered_buyers_coverage'] = True
            else:
                data['covered_buyers_coverage'] = False
        if 'covered_sellers_coverage' in data:
            if data['covered_sellers_coverage'] == 'on':
                data['covered_sellers_coverage'] = True
            else:
                data['covered_sellers_coverage'] = False
        if 'promo_code' in data:
            if data['promo_code'] == False:
                data['promo_code'] = ''
        if 'seller_email' in data:
            if data['seller_email'] == False:
                data['seller_email'] = ''
        if 'seller_phone' in data:
            if data['seller_phone'] == False:
                data['seller_phone'] = ''
        if 'seller_name' in data:
            if data['seller_name'] == False:
                data['seller_name'] = ''
        if 'buyer_email' in data:
            if data['buyer_email'] == False:
                data['buyer_email'] = ''
        if 'buyer_phone' in data:
            if data['buyer_phone'] == False:
                data['buyer_phone'] = ''
        if 'buyer_name' in data:
            if data['buyer_name'] == False:
                data['buyer_name'] = ''
        if data.get('property_state', 0):
            state_id = request.env['res.country.state'].browse(data['property_state'])
            data['pricelist_id'] = request.env['product.pricelist'].get_home_warranty_pricelist_by_state_wise(state_id)
        if not error:
            try:
                home_warranty = request.env['home.warranty'].sudo().create(data)
            except ValueError as e:
                try:
                    error[str(e).split(' ')[3]] = str(e).split("'")[1]
                finally:
                    error_message.append(str(e))
        if error or error_message:
            home_warranty = request.env['home.warranty'].sudo().new(data)
            default_values = {}
            if request.env.user.partner_id != request.env.ref('base.public_partner'):
                default_values['name'] = request.env.user.partner_id.name
                default_values['email'] = request.env.user.partner_id.email
                default_values['realtor'] = request.env.user.partner_id.id
            states = request.env['res.country.state'].search([['enable_home_warranty','=',True]])
            domain = ['|', ['id', '=', request.env.user.partner_id.id],
                                                          ['vendor_type', '=', 'Realtor'], ['active', '=', True],
                                                          ['parent_id', '=', request.env.user.partner_id.parent_id.id],
                                                          ]
            if not request.env.user.partner_id.parent_id:
                domain = [['id', '=', request.env.user.partner_id.id]]
            elif request.env.user.partner_id.parent_id.email == 'info@achosahw.com':
                domain = [['vendor_type', '=', 'Realtor'], ['active', '=', True]]
            realtors = request.env['res.partner'].search(domain)
            addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn')])
            conserve_id, conserve_plus_id = request.env['home.warranty'].sudo()._get_add_on_attribute_value_id()
            rental_addon_id = request.env['home.warranty'].sudo()._get_add_on_noop_attribute_value_id()
            return request.render("achosa.New", {
                'default_values': default_values,
                'home_warranty': home_warranty,
                'add_ons': addons,
                'error': error,
                'error_message': error_message,
                'states': states,
                'realtors': realtors,
                'conserve_id': conserve_id,
                'conserve_plus_id': conserve_plus_id,
                'rental_addon_id': rental_addon_id
            })
        else:
            try:
                if data['covered_buyer_addons']:
                    home_warranty['covered_buyer_addons'] = data['covered_buyer_addons']
                sales_id = 1
                if request.env.user.user_id.id:
                    sales_id = request.env.user.user_id.id
                partner_id = request.env.user.partner_id.id
                error_message = home_warranty.check_ready_for_subscription(sales_id,partner_id)
            except ValueError as e:
                error_message.append(str(e))
        product_ids = home_warranty[0].product.with_context({"pricelist": home_warranty.pricelist_id.id})
        if error or error_message:
            if len(error_message) > 0 and error_message[0].endswith("Applied") and home_warranty.promo:
                total = 0
                for product in product_ids:
                    total += product.price
                return request.render("achosa.portal_home_warranty_valid_promo", {
                        'page_name': 'Home Warranty Order',
                        'products': product_ids,
                        'total': total,
                        'home_warranty': home_warranty,
                        'success_message': error_message,
                        'action': '/my/home_warranties/%s' % home_warranty.id
                    })

            else:
                states = request.env['res.country.state'].search([['enable_home_warranty', '=', True]])
                domain = ['|', ['id', '=', request.env.user.partner_id.id],
                          ['vendor_type', '=', 'Realtor'], ['active', '=', True],
                          ['parent_id', '=', request.env.user.partner_id.parent_id.id],
                          ]
                if not request.env.user.partner_id.parent_id:
                    domain = [['id', '=', request.env.user.partner_id.id]]
                elif request.env.user.partner_id.parent_id.email == 'info@achosahw.com':
                    domain = [['vendor_type', '=', 'Realtor'], ['active', '=', True]]
                realtors = request.env['res.partner'].search(domain)
                addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn')])
                return request.render("achosa.portal_home_warranty_page", {
                        'states': states,
                        'realtors': realtors,
                        'page_name': 'Home Warranty Order',
                        'home_warranty': home_warranty,
                        'add_ons': addons,
                        'error': error,
                        'error_message': error_message,
                        'action': '/my/home_warranties/%s' % home_warranty.id
                    })
        else:
            domain = [['id', '=', request.env.user.partner_id.id]]
            user = request.env['res.partner'].search(domain).sudo()
            if user:
                for u in user:
                    if not u.vendor_type:
                        u.write({'vendor_type': 'Realtor'})
                        #u.write({'supplier': True})
            
            body = ""
            if home_warranty.covered_seller_product_id:
                body += "<h2>Thank you for your Seller Order:</h2>"
                body += "You will be receiving a confirmation e-mail shortly"

            if home_warranty.covered_buyer_product_id:
                body += "<h2>Thank you for your Buyer Order:</h2>"
                body += "You will be receiving a confirmation e-mail shortly"

            return request.render("achosa.portal_home_warranty_success", {
                'page_name': 'Home Warranty Order',
                'home_warranty': home_warranty,
                'body':body
            })

    @http.route(['/my/mail.mail'], type='http', auth="user", methods=['POST'], website=True)
    def portal_my_home_warranty_msg(self, **post):
        """
        Post message to home warranty
        :param post: data to post
        :return: JSON with message id
        """
        # TODO: handle error
        home_warranty_id = post['home_warranty_id']
        partner = request.env.user.partner_id
        HomeWarrranty = request.env['home.warranty']
        domain = [('id','=',home_warranty_id),('realtor_contact','=',partner.id)]
        if partner.parent_id and partner.vendor_type and partner.vendor_type == 'Coordinator':
            domain = [('id','=',home_warranty_id),('realtor_contact.parent_id','=',partner.parent_id.id)]
        home_warranty = HomeWarrranty.sudo().search(domain)
        msg = home_warranty[0].message_post(body=escape(post['body']).replace('\n','<br/>'),author_id=partner.id,email_from=partner.email,
                                            message_type='comment',subtype_id=1,
                                            subject='RE: %s' % home_warranty[0].name)
        return json.dumps({'id':msg.id})

    def _get_achosa_portal_customers_domain(self, partner_id, quotation_order=False):
        """
            @Usage: Prepare the domain to search the sale orders based on vendor type Co-ordinator / Realtor
            @Ticket: AO-857 | Contact - Non-Coordinator Contact Seeing Sales Orders for other people.
            #INC-7806: Fwd: SO/60335
            :param partner_id: res.partner()
            :return: domain -> list of tuple
        """
        domain = [('state', 'in', ['sale', 'cancel'])] if quotation_order else [('state', 'in', ['sent', 'done'])]
        if partner_id.vendor_type == 'Coordinator':
            domain.append(('message_partner_ids', 'child_of', [partner_id.commercial_partner_id.id]))
        else:
            domain.append(('partner_id', 'child_of', partner_id.ids))
        return domain

    def _prepare_home_portal_values(self, counters):
        """
            @Override: override this method and update the domain to search the sales order count
                Default Base Addons Path: /odoo/addons/sale/controllers/portal.py
            @Ticket: AO-857 | Contact - Non-Coordinator Contact Seeing Sales Orders for other people.
            #INC-7806: Fwd: SO/60335
            :return: values -> Dict.
        """
        values = super(PortalHomeWarranty, self)._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        SaleOrder = request.env['sale.order']
        quotation_count = SaleOrder.search_count(
            self._get_achosa_portal_customers_domain(partner_id=partner, quotation_order=True)) \
            if SaleOrder.check_access_rights('read', raise_exception=False) else 0
        order_count = SaleOrder.search_count(
            self._get_achosa_portal_customers_domain(partner_id=partner)) \
            if SaleOrder.check_access_rights('read', raise_exception=False) else 0

        values.update({
            'quotation_count': quotation_count,
            'order_count': order_count,
        })
        return values

    #
    # Quotations and Sales Orders
    #

    @http.route(['/my/quotes', '/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_quotes(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """
            @Override: override this method and update the domain to search the sales quotations
                Default Base Addons Path: /odoo/addons/sale/controllers/portal.py
            @Ticket: AO-857 | Contact - Non-Coordinator Contact Seeing Sales Orders for other people.
            #INC-7806: Fwd: SO/60335
            :return: render the template sale.portal_my_quotations
        """
        _logger.info(f"Method: portal_my_quotes, Page: [{page}], Date Begin: [{date_begin}], Date End: [{date_end}], "
                     f"Sort By: [{sortby}], Kwargs: [{kw}]")
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = self._get_achosa_portal_customers_domain(partner_id=partner, quotation_order=True)
        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }

        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('sale.order', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        quotation_count = SaleOrder.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/quotes",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=quotation_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        quotations = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_quotations_history'] = quotations.ids[:100]

        values.update({
            'date': date_begin,
            'quotations': quotations.sudo(),
            'page_name': 'quote',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/quotes',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("sale.portal_my_quotations", values)

    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """
            @Override: override this method and update the domain to search the sales order
                Default Base Addons Path: /odoo/addons/sale/controllers/portal.py
            @Ticket: AO-857 | Contact - Non-Coordinator Contact Seeing Sales Orders for other people.
            #INC-7806: Fwd: SO/60335
            :return: render the template sale.portal_my_orders
        """
        _logger.info(f"Method: portal_my_orders, Page: [{page}], Date Begin: [{date_begin}], Date End: [{date_end}], "
                     f"Sort By: [{sortby}], Kwargs: [{kw}]")
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = self._get_achosa_portal_customers_domain(partner_id=partner)
        _logger.info(f"Partner: [{partner.name}], Domain: {domain}")
        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'date_order desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'stage': {'label': _('Stage'), 'order': 'state'},
        }
        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']

        archive_groups = self._get_archive_groups('sale.order', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = SaleOrder.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_orders_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders.sudo(),
            'page_name': 'order',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/orders',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("sale.portal_my_orders", values)

class sale_subscription(http.Controller):

    @http.route(['/my/subscription/<int:account_id>/',
                 '/my/subscription/<int:account_id>/<string:uuid>'], type='http', auth="public", methods=['GET'], website=True)
    def subscription(self, account_id, uuid='', message='', message_class='', **kw):
        account_res = request.env['sale.subscription']
        if uuid:
            account = account_res.sudo().browse(account_id)
            if uuid != account.uuid or account.state == 'cancelled':
                raise NotFound()
            if request.uid == account.partner_id.user_id.id:
                account = account_res.browse(account_id)
        else:
            account = account_res.browse(account_id)

        acquirers = list(request.env['payment.acquirer'].search([
            ('redirect_form_view_id', '!=', False),
            ('allow_tokenization', '=', True)]))
        acc_pm = account.payment_token_id
        part_pms = account.partner_id.payment_token_ids
        display_close = account.template_id.sudo().user_closable and account.state != 'close'
        is_follower = request.env.user.partner_id.id in [follower.partner_id.id for follower in account.message_follower_ids]
        active_plan = account.template_id.sudo()
        if account.recurring_next_date:
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            if account.recurring_rule_type != 'weekly':
                rel_period = relativedelta(datetime.today(), datetime.strptime(str(account.recurring_next_date), '%Y-%m-%d'))
                missing_periods = getattr(rel_period, periods[account.recurring_rule_type]) + 1
            else:
                delta = datetime.today() - datetime.strptime(str(account.recurring_next_date), '%Y-%m-%d')
                missing_periods = delta.days / 7
        else:
            missing_periods = ""
        # dummy, action = request.env['ir.model.data'].check_object_reference('sale_subscription', 'sale_subscription_action')
        action = request.env.ref('sale_subscription.sale_subscription_action')
        values = {
            'account': account,
            'template': account.template_id.sudo(),
            'display_close': display_close,
            'is_follower': is_follower,
            'close_reasons': request.env['sale.subscription.close.reason'].search([]),
            'missing_periods': missing_periods,
            'payment_mandatory': active_plan.payment_mandatory,
            'user': request.env.user,
            'acquirers': acquirers,
            'acc_pm': acc_pm,
            'part_pms': part_pms,
            'is_salesman': request.env['res.users'].sudo(request.uid).has_group('sales_team.group_sale_salesman'),
            'action': action,
            'message': message,
            'message_class': message_class,
            'change_pm': kw.get('change_pm') != None,
            'pricelist': account.pricelist_id.sudo(),
            'submit_class':'btn btn-primary btn-sm mb8 mt8 pull-right',
            'submit_txt':'Pay Subscription',
            'bootstrap_formatting':True,
            'return_url':'/my/subscription/' + str(account_id) + '/' + str(uuid),
        }

        history = request.session.get('my_subscriptions_history', [])
        values.update(get_records_pager(history, account))
        return request.render("sale_subscription.subscription", values)
