# -*- coding: utf-8 -*-
# from odoo import http


# class StagingInit(http.Controller):
#     @http.route('/staging_init/staging_init', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/staging_init/staging_init/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('staging_init.listing', {
#             'root': '/staging_init/staging_init',
#             'objects': http.request.env['staging_init.staging_init'].search([]),
#         })

#     @http.route('/staging_init/staging_init/objects/<model("staging_init.staging_init"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('staging_init.object', {
#             'object': obj
#         })
