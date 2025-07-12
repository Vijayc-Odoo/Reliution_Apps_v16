# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

import requests
from odoo.http import request
from odoo import http, fields


class RcsContactAddressGooglePlace(http.Controller):

    def get_proper_address(self, results):
        # Initialize fields
        street = city = zip = street2 = country_code = ""
        state = country = False
        for res in results:
            t = res.get('types')[0]
            d = res.get('longText')
            if street and t in ['route','neighborhood']:
                street = street + ","
            if 'route' in t:
                street = d
            if 'locality' in t:
                city = d
            if 'administrative_area_level_1' in t:
                state = d
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
        return {
            'street': street,
            'street2': street2,
            'city': city,
            'state': state,
            'zip': zip,
            'country': country,
            'country_code':country_code,
        }

    # this method is used to request and search the places
    @http.route('/res_find_gmap/address', type='json', auth='user')
    def rcs_find_gmap_address(self, partial_address):

        company = request.env.user.company_id or request.env.company
        if len(partial_address) < company.rcs_google_api_search_char:
            return []

        if company and company.rcs_is_enable_google_api_key and company.rcs_google_api_key:
            headers = {
                'X-Goog-Api-Key': company.rcs_google_api_key,
                'Content-Type': 'application/json',
                # 'X-Goog-FieldMask': 'places.id,places.name,places.displayName,places.formattedAddress',
                # 'X-Goog-FieldMask': '*',
                'X-Goog-FieldMask': '',
            }

            payload = {
                'input': partial_address,
                # 'textQuery': partial_address,
                # "pageSize": 5,
                # 'regionCode':'CA',
            }
            url = 'https://places.googleapis.com/v1/places:autocomplete'
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()
            results = result.get('suggestions')
            # results = result.get('places')
            if result:
                places = [{'placeName': res.get('placePrediction').get('text').get('text'),
                           'id': res.get('placePrediction').get('placeId')} for res in results]
                # places = [{'formattedAddress': res.get('formattedAddress'), 'id': res.get('id')} for res in results]
                print(places)
                return places
            return []
        return []

    @http.route("/rcs_detail_gmap/address", type='json', auth='user')
    def rcs_fill_gmap_address(self, address, place_id):
        company = request.env.user.company_id or request.env.company
        if company and company.rcs_is_enable_google_api_key and company.rcs_google_api_key:
            headers = {
                'X-Goog-Api-Key': company.rcs_google_api_key,
                'Content-Type': 'application/json',
                'X-Goog-FieldMask': '*',
                # 'X-Goog-FieldMask': 'id,displayName,formattedAddress,plusCode,addressComponents',
            }

            url = f'https://places.googleapis.com/v1/places/{address}'
            response = requests.get(url, headers=headers)
            result = response.json()
            print(result)
            # self.get_proper_address(result.get('addressComponents'))

        return self.get_proper_address(result.get('addressComponents'))
