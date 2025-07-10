# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

from odoo.http import request
from odoo import http,fields

class RcsContactAddressGooglePlace(http.Controller):

    # this method is used to request and search the places
    @http.route('/res_find_gmap/address',type='json', auth='user')
    def rcs_find_gmap_address(self,partial_address):

        if len(partial_address) < 4:
            return []

        company = request.env.user.company_id or request.env.company
        print(company.rcs_is_enable_google_api_key)