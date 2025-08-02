import logging

from odoo import http, tools, _
from odoo.http import request
from odoo.exceptions import UserError, AccessError, MissingError
from odoo.addons.website_sale.controllers.main import WebsiteSale as ws
from odoo.addons.portal.controllers.portal import CustomerPortal
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from . import portal

_LOGGER = logging.getLogger("##### Achosa #####")


class AchosaCustomerPortal(CustomerPortal):

    def _subscription_get_page_view_values(self, subscription, access_token, **kwargs):
        values = {
            'page_name': 'subscription',
            'subscription': subscription,
            'end_date': subscription.date_start + relativedelta(days=-1, years=1)
        }
        return self._get_page_view_values(subscription, access_token, values, 'my_subscription_history', False, **kwargs)

    @http.route([
        '/my/subscription/cancel/<int:subscription_id>/<access_token>'
    ], type='http', auth="public", website=True)
    def subscription_cancel(self, subscription_id=None, access_token=None, **kw):
        try:
            subscription_sudo = self._document_check_access('sale.subscription', subscription_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = self._subscription_get_page_view_values(subscription_sudo, access_token, **kw)
        return request.render("achosa.confirm_cancel_subscription", values)

    @http.route([
        '/my/subscription/confirm_cancel/<int:subscription_id>'
    ], type='http', auth="public", website=True)
    def subscription_confirm_cancel(self, subscription_id=None, **kw):
        """
            Added just logger nothing else.
        """
        if subscription_id:
            sub_rec = request.env['sale.subscription'].browse(subscription_id).sudo()
            reason_rec = request.env['sale.subscription.close.reason'].search([('cancellation_reason', '=', True)])
            end_date = sub_rec._get_subscription_end_date('cancel')
            values = {
                'date': end_date - timedelta(days=1) if end_date else False,
                'is_cancellation_request': True,
                'close_reason_id': reason_rec and reason_rec.id or False
            }
            _LOGGER.info(f"=== Subscription confirmation field  values: [{values}] ===")
            sub_rec.write(values)
            template = request.env.ref('achosa.subscriber_cancellation_request_mail').sudo()
            if not request.env['mail.message'].search(
                    [['model', '=', 'sale.subscription'], ['res_id', '=', sub_rec.id], ['subject', '=', template.subject]],
                    limit=1):
#             template.sudo().send_mail(sub_rec.id, force_send=True)
                sub_rec.message_post_with_template(template.id, composition_mode='comment')
            return request.render('achosa.cancellation_confirmation_subscription', {})
        return request.render('achosa.cancellation_confirmation_subscription_error', {})


class WebsiteSale(ws):
    # ------------------------------------------------------
    # Extra step
    # ------------------------------------------------------
    @http.route(['/shop/warranty_info'], type='http', auth="public", website=True)
    def warranty_info(self, **kw):

        values, errors = {}, {}
        error_message = False
        if kw.get('property_state', 0):
            kw['property_state'] = int(kw['property_state'])
        # Check that this option is activated
        #extra_step = request.env.ref('achosa.warranty_info_option')
        #if not extra_step.active:
        #    return request.redirect("/shop/checkout")

        # check that cart is valid
        order = request.website.sale_get_order().sudo()
        def_country_id = order.partner_id.country_id
        if not def_country_id:
            def_country_id = request.env['res.country'].search([['name','=','United States']]).id
            order.partner_id.country_id = def_country_id

        # if form posted
        if 'submitted' in kw:
            if not kw.get('accept'):
                errors['accept'] = 'required'
                error_message = ["Please check to accept the Terms and conditions for this home warranty"]
            else:
                data, errors = self.update_data(order,kw)
                if not errors:
                    if order.home_warranty:
                        errors, error_message = self.update_home_warranty(data,
                                                                          order.home_warranty.with_context(no_log=True),
                                                                          errors)
                    else:
                        errors, error_message = self.submit_home_warranty(data, order, errors)
                    self.update_cart_add_ons(order)
                if not errors and not error_message:
                    if kw.get('useProperyAddress') == "on":
                        # Update billing address on Partner if no street address
                        if not order.partner_id.street:
                            if kw.get('street'):
                                order.partner_id.street = kw.get('street')
                            if kw.get('street2'):
                                order.partner_id.street2 = kw.get('street2')
                            if kw.get('city'):
                                order.partner_id.city = kw.get('city')
                            if kw.get('state'):
                                order.partner_id.state_id = int(kw.get('state'))
                            if kw.get('zip'):
                                order.partner_id.zip = kw.get('zip')
                    else:
                        # Update billing address on Partner
                        if kw.get('street'):
                            order.partner_id.street = kw.get('street')
                        if kw.get('street2'):
                            order.partner_id.street2 = kw.get('street2')
                        if kw.get('city'):
                            order.partner_id.city = kw.get('city')
                        if kw.get('state_id'):
                            order.partner_id.state_id = int(kw.get('state_id'))
                        if kw.get('zip'):
                            order.partner_id.zip = kw.get('zip')
                if not errors and not error_message:
                    return request.redirect('/shop/confirm_order')
        partner_id = order.partner_id.id

        terms = []
        addons = {}
        allow_rental = False

        for product in order.order_line.mapped('product_id'):
            for attr in product.attribute_line_ids.mapped('value_ids'):
                attachments = request.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'product.attribute.value'),
                    ('res_id', '=', attr.id)])
                for attach in attachments:
                    terms += attach
                if attr.attribute_id.name == 'Terms':
                    states = attr.states
                if attr.name in ('Single Family Home','Townhome/Condo','New'):
                    allow_rental = True
                    
        rental_addon_id = request.env['home.warranty'].sudo()._get_add_on_noop_attribute_value_id()
        if(len(states) > 0):
            if allow_rental:
                addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn'),
                                                                       ('states.id', '=', states[0].id),
                                                                        ('id','!=',227)])
            else:
                addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn'),
                                                                       ('states.id', '=', states[0].id),
                                                                        ('id','!=',rental_addon_id)])
        
        conserve_id, conserve_plus_id = request.env['home.warranty'].sudo()._get_add_on_attribute_value_id()
        rental_addon_id = request.env['home.warranty'].sudo()._get_add_on_noop_attribute_value_id()
        if errors or error_message:
            _LOGGER.log(logging.INFO, "Order: %s" % order.name)
            _LOGGER.log(logging.WARN, str(errors))
            _LOGGER.log(logging.WARN, str(error_message))
            values = {
                'website_sale_order': order,
                'partner_id': partner_id,
                'checkout': kw,
                'country': def_country_id,
                'countries': request.env['res.country'].search([['name','=','United States']]),
                "states": states,
                'error': errors,
                'error_message': error_message,
                'terms': terms,
                'home_warranty': order.home_warranty or request.env['home.warranty'].sudo().new(),
                'add_ons': addons,
                'street': order.partner_id.street,
                'street2': order.partner_id.street2,
                'city': order.partner_id.city,
                'state': order.partner_id.state_id,
                'zip': order.partner_id.zip,
                'conserve_id': conserve_id,
                'conserve_plus_id': conserve_plus_id,
                'rental_addon_id': rental_addon_id
            }
        else:
            values = {
                'website_sale_order': order,
                'partner_id': partner_id,
                'checkout': order.home_warranty or order.partner_id,
                'country': def_country_id,
                'countries': request.env['res.country'].search([['name','=','United States']]),
                "states": states,
                'error': errors,
                'error_message': error_message,
                'terms': terms,
                'home_warranty': order.home_warranty or request.env['home.warranty'].sudo().new(),
                'add_ons': addons,
                'street': order.partner_id.street,
                'street2': order.partner_id.street2,
                'city': order.partner_id.city,
                'state': order.partner_id.state_id,
                'zip': order.partner_id.zip,
                'conserve_id': conserve_id,
                'conserve_plus_id': conserve_plus_id,
                'rental_addon_id': rental_addon_id
            }

        return request.render("achosa.warranty_info", values)

    @staticmethod
    def get_achosa_property_type(order):
        property_type = ''
        for product_template_attribute_value_id in order.order_line.product_id.product_template_attribute_value_ids:
            if product_template_attribute_value_id.attribute_id.name == 'Property Type':
                property_type = product_template_attribute_value_id.name
                break
        return property_type

    @http.route(['/shop/addons'],type='http', auth="public", website=True)
    def addons(self, **post):
        allow_rental = False
        order = request.website.sale_get_order()
        property_type = self.get_achosa_property_type(order)
        for product in order.order_line.mapped('product_id'):
            for attr in product.attribute_line_ids.mapped('value_ids'):
                if attr.attribute_id.name == 'Terms':
                    states = attr.states
                if attr.name in ('Single Family Home','Townhome/Condo','New'):
                    allow_rental = True
        rental_addon_id = request.env['home.warranty'].sudo()._get_add_on_noop_attribute_value_id()
        if(len(states) > 0):
            if allow_rental:
                addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn'),
                                                                       ('states.id', '=', states[0].id),
                                                                        ('id','!=',227)])
            else:
                addons = request.env['product.attribute.value'].search([('term_product_type', '=', 'AddOn'),
                                                                       ('states.id', '=', states[0].id),
                                                                        ('id','!=',rental_addon_id)])

        pricelist_obj = request.env['product.pricelist']
        res_country_state_obj = request.env['res.country.state']
        property_state_id = request.httprequest.values.get('property_state', 0) or 0
        property_state = res_country_state_obj.browse(int(property_state_id))
        pricelist_id = pricelist_obj.get_home_warranty_pricelist_by_state_wise(property_state)
        ps = ''
        ids = request.env['product.product'].sudo().search([
            ('attribute_line_ids.product_template_value_ids', '=', 'Homeowner')])
        for id in ids:
            value_ids = id.attribute_line_ids.mapped('value_ids')
            for a in value_ids:
                if a.attribute_id.name == "Terms":
                    if a.term_product_type == 'AddOn' and 'Property Type' in value_ids.mapped(
                            'attribute_id.name') and property_type not in id.product_template_attribute_value_ids.mapped(
                        'name'):
                        continue
                    # ps += """$('#{0}_Price').html(" ${1:,.2f}"); //{2}\n """.format(a.id, id.lst_price, id.name)
                    ps += """$('#{0}_Price').html(" ${1:,.2f}"); //{2}\n """.format(a.id, id.with_context({'pricelist':pricelist_id}).price, id.name)

        home_warranty = request.env['home.warranty'].sudo().new()

        if 'covered_buyer_addons' in post:
            home_warranty.covered_buyer_addons = portal.PortalHomeWarranty.validate_covered_buyer_addons(post, True)[
                'covered_buyer_addons']

        return request.render("achosa.HW_add-ons", {
            'home_warranty': home_warranty,
            'add_ons': addons,
            'pricescript': ps
        }) #achosa.sale_terms

    @http.route(['/shop/terms'],type='http', auth="public", website=True)
    def shop_terms(self, **post):
        terms = []
        order = request.website.sale_get_order()
        for line in order.order_line:
            if line.product_id.warranty_terms_id.term_product_type != 'AddOn':
                for a in line.product_id.attribute_line_ids.mapped('value_ids'):
                    if a.attribute_id.name == "Terms":
                        attachments = request.env['ir.attachment'].sudo().search([
                            ('res_model', '=', 'product.attribute.value'),
                            ('res_id', '=', a.id)])
                        for attach in attachments:
                            terms += attach
        if 'covered_buyer_addons' in post:
            covered_buyer_addons = portal.PortalHomeWarranty.validate_covered_buyer_addons(post, True)[
                'covered_buyer_addons']
            for a in covered_buyer_addons:
                if a.attribute_id.name == "Terms":
                    attachments = request.env['ir.attachment'].sudo().search([
                        ('res_model', '=', 'product.attribute.value'),
                        ('res_id', '=', a.id)])
                    for attach in attachments:
                        terms += attach

        return request.render("achosa.sale_terms", {
            'terms': terms,
        })

    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):
        #order = request.website.sale_get_order()
        return request.redirect("/shop/warranty_info")

    @staticmethod
    def update_cart_add_ons(order):
        home_warranty = order.home_warranty
        # Update the home warranty property type, Ticket : AO-747, Comment: below line added
        property_type = WebsiteSale.get_achosa_property_type(order)
        home_warranty.property_type = property_type
        so_products = []
        # Remove products no longer on order
        for line in order.order_line:
            _LOGGER.log(logging.INFO, line.name + ' ' + str(line.subscription_id))
            if line.product_id.warranty_terms_id.term_product_type == 'AddOn' and \
                    line.product_id.warranty_terms_id.id not in home_warranty.covered_buyer_addons.ids:
                line.unlink()
            so_products.append(line.product_id.warranty_terms_id.id)
        # Add new products
        for add_on in home_warranty.covered_buyer_addons.ids:
            if so_products.count(add_on) < 1:
                product_ids = request.env['product.product'].sudo().search([
                    ('attribute_line_ids.product_template_value_ids', '=', 'Homeowner'),
                    ('attribute_line_ids.product_template_value_ids.product_attribute_value_id.id', '=', add_on)])
                product = product_ids
                _LOGGER.info(
                    f"Method: [update_cart_add_ons], Products: {product.ids}, Home Warranty Property Type: [{home_warranty.property_type}]")
                for product_id in product_ids:
                    for product_template_attribute_value_id in product_id.product_template_attribute_value_ids:
                        if product_template_attribute_value_id.attribute_id.name == 'Property Type' \
                                and product_template_attribute_value_id.name == property_type:
                            product = product_id
                            break
                _LOGGER.info(f"Method: [update_cart_add_ons], Product: {product.ids}")
                # Create the sales order lines
                sales_order_line_obj = request.env['sale.order.line'].sudo()
                sol_id = sales_order_line_obj.create({
                    "product_id": product.id,
                    "product_uom_qty": 1,
                    "discount": 0,
                    "order_id": order.id
                }
                )
        return

    @staticmethod
    def update_data(order, post_data):
        model_record = request.env['ir.model'].sudo().search(
            [('model', '=', 'home.warranty'), ('website_form_access', '=', True)])
        #authorized_fields = model_record.sudo()._get_form_writable_fields()
        data = {}
        error = dict()
        fields = ['owner_name', 'owner_email', 'owner_phone', 'property_street', 'property_city', 'property_state',
                  'property_zip']
        for f in fields:
            if post_data.get(f):
                data[f] = post_data.get(f)
            else:
                error[f] = "required"
        if post_data.get("property_street2"):
            data["property_street2"] = post_data.get("property_street2")
        data["covered_owners_coverage"] = True
        data["covered_buyer_term"] = '12'
        for product in order.order_line.mapped('product_id'):
            for attr in product.attribute_line_ids.mapped('value_ids'):
                if attr.attribute_id.name == 'Terms':
                    data['covered_owner_product_id'] = attr.id
        if 'covered_buyer_addons' in post_data:
            data['covered_buyer_addons'] = portal.PortalHomeWarranty.validate_covered_buyer_addons(post_data, True)['covered_buyer_addons']
            if data['covered_buyer_addons'] == "":
                data['covered_buyer_addons'] = [[]]
        return data, error

    @staticmethod
    def submit_home_warranty(data, order, errors):
        crm_lead_obj = request.env['crm.lead'].sudo()
        error = errors or dict()
        error_message = []
        home_warranty = False
        data['name'] = 'New'
        try:
            order.order_type = "Owner"
            # Update the home warranty property type, Ticket : AO-747, Comment: below line added
            property_type = WebsiteSale.get_achosa_property_type(order)
            data['property_type'] = property_type
            _LOGGER.info(f"Method: [submit_home_warranty], Data: [{data}], Order: [{order}]")
            home_warranty = request.env['home.warranty'].sudo().create(data)
            
            if 'covered_buyer_addons' in data:
                home_warranty['covered_buyer_addons'] = data['covered_buyer_addons']
            if home_warranty:
                order.home_warranty = home_warranty

                home_warranty._compute_orders()
                home_warranty._get_invoiced()

                if data['owner_name'] != "":
                    if home_warranty['owner_contact']:
                        home_warranty.update_customer_contact(data['owner_contact'],
                            data['owner_name'],
                            data['owner_email'],
                            data['owner_phone'])
                        home_warranty['owner_email'] = data['owner_email']
                        home_warranty['owner_phone'] = data['owner_phone']
                    else:
                        home_warranty['owner_contact'] = home_warranty.create_customer_contact(
                            data['owner_name'],
                            data['owner_email'],
                            data['owner_phone']).id
                        home_warranty['owner_email'] = data['owner_email']
                        home_warranty['owner_phone'] = data['owner_phone']
                if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
                    order.partner_id = home_warranty['owner_contact']
                    order.partner_invoice_id = home_warranty['owner_contact']
                realtor_contact = home_warranty.realtor_contact
                if realtor_contact:
                    lead_ids = crm_lead_obj.get_hw_partner_lead_ids(realtor_contact)
                    if not lead_ids:
                        crm_lead_obj.create_hw_lead(home_warranty, realtor_contact, user_id=order.user_id.id)
                    for lead_id in lead_ids:
                        lead_id._update_hw_lead_status(realtor_contact)
        except ValueError as e:
            try:
                error[str(e).split(' ')[3]] = str(e).split("'")[1]
            finally:
                error_message.append(str(e))
        except UserError as e:
            error_message.append(str(e))

        return error, error_message

    @staticmethod
    def update_home_warranty(data, home_warranty, errors):
        error = errors or dict()
        error_message = []
        data['property_state'] = int(data['property_state'])
        try:
            home_warranty.sudo().write(data)
            if 'covered_buyer_addons' in data:
                home_warranty['covered_buyer_addons'] = data['covered_buyer_addons']
            home_warranty._compute_orders()
            home_warranty._get_invoiced()

            if home_warranty['owner_name']:
                if home_warranty['owner_contact']:
                    home_warranty.update_customer_contact(home_warranty['owner_contact'],
                        home_warranty['owner_name'],
                        home_warranty['owner_email'],
                        home_warranty['owner_phone'])
                else:
                    home_warranty['owner_contact'] = home_warranty.create_customer_contact(
                        home_warranty['owner_name'],
                        home_warranty['owner_email'],
                        home_warranty['owner_phone']).id
        except ValueError as e:
            try:
                error[str(e).split(' ')[3]] = str(e).split("'")[1]
            finally:
                error_message.append(str(e))
        except UserError as e:
            error_message.append(str(e))

        return error, error_message

    @http.route(['/terms_and_conditions'], type='http', auth="public", website=True)
    def terms_page(self, **post):
        states = request.env['res.country.state'].sudo().search([['enable_home_warranty', '=', True]])
        product_attributes = request.env['product.attribute.value'].sudo()\
            .search([('state','=','Published'),('attachment_ids','!=',False)])
        return request.render("achosa.terms_page", {
            'states': states,
            'product_attributes': product_attributes
        })

    @http.route(['/terms_and_conditions/<string:state>'], type='http', auth="public", website=True)
    def terms_page_state(self, state, **post):
        states = request.env['res.country.state'].sudo().search([['enable_home_warranty', '=', True]])
        product_attributes = request.env['product.attribute.value'].sudo() \
            .search([('state', '=', 'Published'), ('attachment_ids', '!=', False),
                     ('states.code','=',state)])
        return request.render("achosa.terms_page", {
            'states': states,
            'product_attributes': product_attributes
        })

    @http.route(['/online-brochure'], type='http', auth="public", website=True)
    def online_brochure(self, **post):
        states = request.env['res.country.state'].sudo().search([['enable_home_warranty', '=', True]])
        product_attributes_current = request.env['product.attribute.value'].sudo()\
            .search([('name','ilike','Online Brochure Current')])
        product_attributes_advantage = request.env['product.attribute.value'].sudo()\
            .search([('name','ilike','Online Brochure Advantage')])
        return request.render("website.online-brochure", {
            'states': states,
            'product_attributes_current': product_attributes_current,
            'product_attributes_advantage': product_attributes_advantage
        })
