# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
import logging

_LOGGER = logging.getLogger("##### Renewal Term Sales #####")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @staticmethod
    def _get_renewal_term(**kwargs):
        """
            This method return the ### Renewal Term ### based on key getting from website template.
            :param kwargs: Keyword Arguments, Example: {'renewal_term': 'Yearly', ...}, Type: Dict.
            :return: ### Renewal Term ###, Type: String
        """
        return '12' if kwargs.get('renewal_term') == 'Yearly' else '1'

    @staticmethod
    def _get_renewal_term_internal_reference(default_code, renewal_term):
        default_code = default_code.strip()
        if renewal_term == '12':
            if not default_code.__contains__('12-R'):
                default_code = default_code[0:-1] + "12-R"
        if renewal_term == '1':
            if default_code.__contains__('12-R'):
                default_code = default_code.replace('12-R', 'R')

        return default_code

    def set_owner_renewal_product(self):
        """ @Usage: Find correct renewal products for corresponding add-on products and set it to order line.
            @Ticket: AO-1004 | NOOP Renewal Fix
            :return: True
        """
        product_category_id = self.env['product.category'].search([('name', '=ilike', 'Home Warranties')], limit=1)
        product_adddon_category_id = self.env['product.category'].search([('name', '=ilike', 'Add-Ons')], limit=1)
        home_owner_product_id = self.order_line.product_id.filtered(
            lambda product_id: product_id.categ_id.id == product_category_id.id)

        for line in self.order_line:
            line_product_id = line.product_id
            if line_product_id == home_owner_product_id:
                continue
            addon_product_id = line_product_id.find_property_type_product(home_owner_product_id) if line_product_id.categ_id.id == product_adddon_category_id.id else line_product_id
            if line.product_id == addon_product_id:
                continue
            else:
                line.create_renewal_sale_order_line(renewal_product_id=addon_product_id)
                line.unlink()
        return True

    def _search_renewal_product(self, product_id, renewal_term):
        """
            This method search the odoo product based on product_id and renewal_term  and return that product
            :param product_id: product.product()
            :param renewal_term: Renewal Term, Example: '12', '1', etc.., Type: String
            :return: product.product()
        """
        default_code = self._get_renewal_term_internal_reference(product_id.default_code, renewal_term)
        if product_id.default_code.strip() == default_code.strip():
            return product_id
        return self.env['product.product'].search([('default_code', '=ilike', default_code)], limit=1)

    # def _search_renewal_product(self, product_id, renewal_term):
    #     """
    #         This method search the odoo product based on product_id and renewal_term  and return that product
    #         :param product_id: product.product()
    #         :param renewal_term: Renewal Term, Example: '12', '1', etc.., Type: String
    #         :return: product.product()
    #     """
    #     product_variant_id = self.env['product.product']
    #     new_term_value_id = self.env['product.attribute.value'].search(
    #         [('name', '=', renewal_term), ('attribute_id.name', '=', 'Renewal Term')], limit=1)
    #     product_attribute_value_ids = product_id.product_template_attribute_value_ids.filtered(
    #         lambda attribute_value_id: attribute_value_id.attribute_id.name != 'Renewal Term').mapped('product_attribute_value_id')
    #     product_attribute_value_ids += new_term_value_id
    #     for variant_id in product_id.product_variant_ids:
    #         if set(variant_id.product_template_attribute_value_ids.ids) == set(
    #                 product_attribute_value_ids.ids):
    #             product_variant_id = variant_id
    #             break
    #     return product_variant_id

    def update_renewal_order_lines(self, **kwargs):
        """
            This method perform below operations:
                - Create the new sale order line if the product found based on renewal term and existing
                sale order line product attribute values and unlink the existing sale order line as well
                - It will skip to create the sale order line if the renewal product and existing
                sale order line product is same
                - If any of one renewal product not found from the sale order lines then this method
                can't create the sale order lines it will prepare the mismatch order lines list and return it.
            :param kwargs: Keyword Arguments, Example: {'renewal_term': 'Yearly', ...}, Type: Dict.
            :return: mismatch_order_line_ids -> List or Boolean
        """
        self.ensure_one()
        renewal_term = self._get_renewal_term(**kwargs)
        mismatch_order_line_ids, order_lines_info_dict = [], {}
        for order_line in self.order_line:
            product_id = order_line.product_id
            renewal_product_id = self._search_renewal_product(product_id, renewal_term)
            if not renewal_product_id:
                mismatch_order_line_ids.append(order_line.id)
                continue
            if renewal_product_id.id == product_id.id:
                continue
            order_lines_info_dict.update({order_line: renewal_product_id})
        if mismatch_order_line_ids:
            return mismatch_order_line_ids

        _LOGGER.info(
            f"\n\nSale Order: [{self.name}], Sale Order With New Renewal Product Info: [{order_lines_info_dict}]]\n\n")
        for order_lines_id, renewal_product_id in order_lines_info_dict.items():
            order_lines_id.create_renewal_sale_order_line(renewal_product_id)
            order_lines_id.unlink()
        return True

    def get_renewal_term_buttons_status(self):
        """
            This method is return the renewal term button status as True  if any of 1 product is not a renewal term
            product from sale order line.
            :return: renewal_term_button_visible -> Boolean
        """
        renewal_term_buttons_visible = False
        for order_line in self.order_line:
            default_code = order_line.product_id.default_code
            if default_code and default_code.strip().lower().endswith('-r'):
                renewal_term_buttons_visible = True
                break
        _LOGGER.info(f"Renewal Term Button Visible Status : [{renewal_term_buttons_visible}]")
        return renewal_term_buttons_visible

    def get_order_renewal_term(self):
        """
            This method is return the order renewal term Either 'Yearly' OR 'Monthly'
            :return: order_renewal_term -> String
        """
        order_renewal_term = ""
        order_renewal_yearly_count = 0
        order_renewal_monthly_count = 0
        order_lines = self.order_line
        for order_line in order_lines:
            if not order_line.product_id.default_code:
                break
            default_code = order_line.product_id.default_code.strip().lower()
            if default_code.endswith('12-r'):
                order_renewal_yearly_count += 1
                continue
            if default_code.endswith('-r'):
                order_renewal_monthly_count += 1
        if len(order_lines) == order_renewal_yearly_count:
            order_renewal_term = "Yearly"
        if len(order_lines) == order_renewal_monthly_count:
            order_renewal_term = "Monthly"
        return order_renewal_term
