# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HWCouponApplyCode(models.TransientModel):
    _name = 'home.warranty.coupon.apply.code'
    _rec_name = 'coupon_code'
    _description = "Coupon entry for home warranty"

    coupon_code = fields.Char(string="Coupon", required=True)


    def process_coupon(self):
        """
        Apply the entered coupon code if valid, raise an UserError otherwise.
        """
        home_warranty = self.env['home.warranty'].browse(self.env.context.get('active_id'))
        error_status = self.apply_coupon(home_warranty, self.coupon_code)
        if error_status.get('error', False):
            raise UserError(error_status.get('error', False))
        if error_status.get('not_found', False):
            raise UserError(error_status.get('not_found', False))

    def apply_coupon(self, rec, coupon_code):
        error_status = {}
        coupon_code = coupon_code.upper()
        program = self.env['coupon.program'].search([('promo_code', '=', coupon_code)])
        if not program:
            return {'not_found': _('Promo %s not found' % coupon_code)}
        error_status = program._check_hw_promo_code(rec, coupon_code)
        if not error_status.get('error', False):
            rec.promo = program
            rec.promo_code = coupon_code
        return error_status
