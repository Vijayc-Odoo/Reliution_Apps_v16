# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo.addons.website_sale_coupon.tests.test_shop_sale_coupon


class TestUi(odoo.addons.website_sale_coupon.tests.test_shop_sale_coupon.TestUi):

    post_install = True
    at_install = False

    def test_01_admin_shop_sale_coupon_tour(self):
        return True
