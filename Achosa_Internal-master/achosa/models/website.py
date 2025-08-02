# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, tools, SUPERUSER_ID, _

from odoo.http import request
from odoo.addons.website.models import ir_http
from odoo.addons.http_routing.models.ir_http import url_for

# logger = logging.getLogger(__name_)


class Website(models.Model):
    _inherit = 'website'

    def get_current_pricelist(self):
        pl = super().get_current_pricelist()
        if request.session.get('category_state'):
            pricelist_id = request.env['product.pricelist'].search([('state_ids', '=', request.session['category_state'])], order='write_date desc', limit=1)
            if pricelist_id:
                pl = pricelist_id
        return pl