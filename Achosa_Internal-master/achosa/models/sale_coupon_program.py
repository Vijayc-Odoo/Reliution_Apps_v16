# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _
from datetime import datetime
import logging

_logger = logging.getLogger("##### Achosa #####")


class SaleCouponProgram(models.Model):
    _inherit = "coupon.program"

    rule_home_warranty_domain = fields.Char(string="Based on Home Warranty",
                                       help="Coupon program will work for filtered home warranties only")

    rule_home_warranty_help = fields.Char(string="Home Warranty Help Text",
                                       help="Display this message when promo does not meet criteria")

    cost = fields.Float(string="Realtor Fee",
                        help="Amount paid to realtor for entering order")

    def _check_hw_promo_code(self, hw, coupon_code):
        """
        Validate the promo code
        :param hw: home warranty order to check against
        :param coupon_code: promo code to validate
        :return:
        """
        message = {}
        if self.maximum_use_number != 0 and self.order_count >= self.maximum_use_number:
            message = {'error': ['Promo code %s has been expired.' % coupon_code]}
        elif (self.rule_date_from and self.rule_date_from > datetime.now()) or \
                (self.rule_date_to and datetime.now() > self.rule_date_to):
            message = {'error': ['Promo %s has been expired.' % coupon_code]}
        elif self.rule_home_warranty_domain and not hw.search_count(eval(self.rule_home_warranty_domain) + [('id', '=', hw.id)]):
            message = {'error': ['Promo %s not valid on this order' % coupon_code, " " +
                                 (self.rule_home_warranty_help or "")]}
        elif self.rule_products_domain:
            productExists = False
            products = self.env['product.product'].search(eval(self.rule_products_domain))
            count = 0
            for p in products:
                if p in hw.product_buyer:
                    count += 1
            if count != len(hw.product_buyer):
                message = {'error': ['Promo %s not valid on this order' % coupon_code, " " +
                                 (self.rule_home_warranty_help or "")]}
            
        return message

    @api.model
    def create(self, vals):
        program = super(SaleCouponProgram, self).create(vals)
        # neg mil worse than strike out issue, see parent object
        program.discount_line_product_id.lst_price = 0
        program.discount_line_product_id.default_code = "promo_" + str(program.reward_type) + "_" + str(program.promo_code)
        return program
    def write(self, vals):
        # UPPERCASE promo code
        if vals.get('promo_code'):
            vals['promo_code'] = vals.get('promo_code').upper()
        res = super(SaleCouponProgram, self).write(vals)
        return res
