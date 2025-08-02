# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_renewal_sale_order_line_values(self, renewal_product_id):
        """
           This method prepare the sale order line information and return it.
           :param renewal_product_id: product.product()
           :return: Dict.
       """
        return {
            'product_id': renewal_product_id.id,
            'order_id': self.order_id.id,
            'company_id': self.order_id.company_id.id,
            'product_uom': renewal_product_id.uom_id.id,
            'name': renewal_product_id.name,
        }

    def create_renewal_sale_order_line(self, renewal_product_id):
        """
           This method create the sale order line and return it.
           :param renewal_product_id: product.product()
           :return: sale.order.line().
       """
        sale_order_line_values = self._prepare_renewal_sale_order_line_values(renewal_product_id)
        tmp_sale_line = self.new(sale_order_line_values)
        tmp_sale_line.product_id_change()
        sale_order_line_values = self._convert_to_write(
            {name: tmp_sale_line[name] for name in tmp_sale_line._cache})
        sale_order_line_values.update({
            'product_uom_qty': self.product_uom_qty,
        })
        return self.create(sale_order_line_values)
