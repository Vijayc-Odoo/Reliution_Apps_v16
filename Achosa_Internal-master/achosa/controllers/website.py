# -*- coding: utf-8 -*-

from odoo import models
from odoo.http import request
from odoo import http, tools, _
from odoo.addons.website_sale.controllers.main import WebsiteSale

class Website(models.Model):
    _inherit = 'website'

    def sale_product_domain(self):
        # remove product without category from the website content grid and list view
        return ['&'] + super(Website, self).sale_product_domain() + \
                   ['!',('public_categ_ids', '=', False)]
    

class WebsiteSale(WebsiteSale):
    _inherit = 'WebsiteSale'
    
    def sitemap_shop(env, rule, qs):
        return super().sitemap_shop(env, rule, qs)
    
    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        # configure the default state in System Parameters "default.product.public.category"
        if category==None and search=='':
            category = request.env["ir.config_parameter"].sudo().get_param('default.product.public.category')
        elif search != '':
            #default to search by stateif searching
            category = 15
        category_id = request.env['product.public.category'].browse(int(category))
        request.session.update({'category_state': category_id.state_id.id})
        return super().shop(page,category,search,ppg,post=post)
        
