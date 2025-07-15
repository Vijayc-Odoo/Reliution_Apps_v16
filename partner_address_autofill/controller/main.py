# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

import requests
from odoo.http import request
from odoo import http, fields

URL = 'https://places.googleapis.com/v1/places'

class RcsContactAddressGooglePlace(http.Controller):

    # this method is used to prepare data in proper formate and make dicnory
    def get_proper_address(self, results):
        # Initialize fields
        street = city = zip = street2 = country_code = state_code = ""
        state = country = state_id = country_id = False
        for res in results:
            t = res.get('types')[0]
            d = res.get('longText')
            if street and t in ['route', 'neighborhood']:
                street = street + ","
            if 'route' in t:
                street = d
            if 'locality' in t:
                city = d
            if 'administrative_area_level_1' in t:
                state = d
                state_code = res.get('shortText')
            if 'postal_code' in t:
                zip = d
            if 'country' in t:
                country = d
                country_code = res.get('shortText')
            if street2 and t in ['neighborhood', 'sublocality_level_1', 'sublocality_level_2']:
                street2 = street2 + ","
            if 'neighborhood' in t:
                street = street + d
            if 'sublocality_level_1' in t:
                street2 = street2 + d
            if 'sublocality_level_2' in t:
                street2 = street2 + d
            print(t, d)
        if state:
            state_id = request.env['res.country.state'].search([('name', '=', state), ('code', '=', state_code)]).id
        if country_code:
            country_id = request.env['res.country'].search([('name', '=', country), ('code', '=', country_code)]).id

        return {
            'street': street,
            'street2': street2,
            'city': city,
            'zip': zip,
            'country': country_id or False,
            'state': state_id or False,
            'country_code': country_code,
        }

    # this method is used to request and search the places
    @http.route('/res_find_gmap/address', type='json', auth='user')
    def rcs_find_gmap_address(self, partial_address):

        company = request.env.user.company_id or request.env.company
        if len(partial_address) < company.rcs_google_api_search_char:
            return []

        country_code = False
        if company.rcs_google_country:
            country_code = company.rcs_google_country.code

        if company and company.rcs_is_enable_google_api_key and company.rcs_google_api_key:
            headers = {
                'X-Goog-Api-Key': company.rcs_google_api_key,
                'Content-Type': 'application/json',
                'X-Goog-FieldMask': 'suggestions.placePrediction.text.text,suggestions.placePrediction.placeId'
            }

            payload = {
                'input': partial_address,
                'includedRegionCodes':country_code or ""
            }

            response = requests.post(f'{URL}:autocomplete', headers=headers, json=payload)
            result = response.json()
            results = result.get('suggestions')
            if result:
                places = [{'placeName': res.get('placePrediction').get('text').get('text'),
                           'id': res.get('placePrediction').get('placeId')} for res in results]
                return places
            return []
        return []

    # this method is used to request and search by place id and prepare the address
    @http.route("/rcs_detail_gmap/address", type='json', auth='user')
    def rcs_fill_gmap_address(self, address, place_id):
        company = request.env.user.company_id or request.env.company
        if company and company.rcs_is_enable_google_api_key and company.rcs_google_api_key:
            headers = {
                'X-Goog-Api-Key': company.rcs_google_api_key,
                'Content-Type': 'application/json',
                'X-Goog-FieldMask': 'id,name,displayName,formattedAddress,addressComponents',
            }

            response = requests.get(f'{URL}/{place_id}', headers=headers)
            result = response.json()
            print(result)
            if not result:
                return []
        return self.get_proper_address(result.get('addressComponents'))
