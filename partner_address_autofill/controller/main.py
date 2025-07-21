# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

import requests
from odoo.http import request
from odoo import http, fields
from odoo.exceptions import ValidationError

URL = 'https://places.googleapis.com/v1/places'

class RcsContactAddressGooglePlace(http.Controller):

    def get_proper_address1(self, fields_key,widget_field_name, result):
        data = {
            'street': '', 'street2': '', 'city': '', 'zip': '',
            'state_name': '', 'state_code': '', 'country_name': '', 'country_code': ''
        }
        results=result.get('addressComponents')
        for res in results:
            type = res.get('types', [''])[0]
            long = res.get('longText', '')
            short = res.get('shortText', '')

            if type == 'route':
                data['street'] = long
            if type == 'locality':
                data['city'] = long
            if type == 'postal_code':
                data['zip'] = long
            if type == 'administrative_area_level_1':
                data['state_name'] = long
                data['state_code'] = short
            if type == 'country':
                data['country_name'] = long
                data['country_code'] = short
            if type == 'neighborhood':
                data['street'] += (", " if data['street'] else "") + long
            if type == 'sublocality_level_1' or type == 'sublocality_level_2':
                data['street2'] += (", " if data['street2'] else "") + long

        state_id = request.env['res.country.state'].search([
            ('name', '=', data['state_name']),
            ('code', '=', data['state_code'])
        ], limit=1).id or False

        country_id = request.env['res.country'].search([
            ('name', '=', data['country_name']),
            ('code', '=', data['country_code'])
        ], limit=1).id or False

        address = {}

        if "STREET" in fields_key:
            address[fields_key["STREET"]] = data["street"]
        if "STREET2" in fields_key:
            address[fields_key["STREET2"]] = data["street2"]
        if "CITY" in fields_key:
            address[fields_key["CITY"]] = data["city"]
        if "ZIP" in fields_key:
            address[fields_key["ZIP"]] = data["zip"]
        if "STATE" in fields_key:
            address[fields_key["STATE"]] = [state_id] if state_id else [False]
        if "COUNTRY" in fields_key:
            address[fields_key["COUNTRY"]] = [country_id] if country_id else [False]
        return address

        # return {
        #     fields_key["STREET"]: data["street"],
        #     fields_key["STREET2"]: data["street2"],
        #     fields_key["CITY"]: data["city"],
        #     fields_key["ZIP"]: data["zip"],
        #     # fields_key["STATE"]: [state_id],
        #     # fields_key["COUNTRY"]: [country_id],
        #     # widget_field_name:""
        # }

    # this method is used to prepare data in proper formate and make dicnory
    # def get_proper_address(self,res, results):
    #     # Initialize fields
    #     fields_key = res
    #
    #     street = city = zip = street2 = country_code = state_code = ""
    #     state = country = state_id = country_id = False
    #     for res in results:
    #         t = res.get('types')[0]
    #         d = res.get('longText')
    #         if street and t in ['route', 'neighborhood']:
    #             street = street + ","
    #         if 'route' in t:
    #             street = d
    #         if 'locality' in t:
    #             city = d
    #         if 'administrative_area_level_1' in t:
    #             state = d
    #             state_code = res.get('shortText')
    #         if 'postal_code' in t:
    #             zip = d
    #         if 'country' in t:
    #             country = d
    #             country_code = res.get('shortText')
    #         if street2 and t in ['neighborhood', 'sublocality_level_1', 'sublocality_level_2']:
    #             street2 = street2 + ","
    #         if 'neighborhood' in t:
    #             street = street + d
    #         if 'sublocality_level_1' in t:
    #             street2 = street2 + d
    #         if 'sublocality_level_2' in t:
    #             street2 = street2 + d
    #         print(t, d)
    #     if state:
    #         state_id = request.env['res.country.state'].search([('name', '=', state), ('code', '=', state_code)]).id
    #     if country_code:
    #         country_id = request.env['res.country'].search([('name', '=', country), ('code', '=', country_code)]).id
    #
    #     B = {
    #         fields_key['STREET']: street,
    #         fields_key['STREET2']: street2,
    #         fields_key['CITY']: city,
    #         fields_key['ZIP']: zip,
    #         # fields_key['STATE']: [state_id or False],
    #         # fields_key['COUNTRY']: [country_id or False],
    #     }
    #     return B
        # return {
        #     'street': street,
        #     'street2': street2,
        #     'city': city,
        #     'zip': zip,
        #     'country': country_id or False,
        #     'state': state_id or False,
        #     'country_code': country_code,
        # }

    # this method is used to request and search the places
    @http.route('/res_find_gmap/address', type='json', auth='user')
    def rcs_find_gmap_address(self, partial_address):

        company = request.env.user.company_id or request.env.company
        if len(partial_address) < company.rcs_google_api_search_char:
            return []

        # self.env['ir.model'].search([('name')])

        # self.env['rcs.address.field.mapping']
        country_code = False
        if company.rcs_google_country1:
            country_code = company.rcs_google_country1.mapped('code')

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
    def rcs_fill_gmap_address(self, address, place_id,resModel,widget_field_name):
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
            model = request.env['ir.model'].search([('model', '=', resModel)])
            field_ids=request.env['ir.model.fields'].search([('model_id','=',model.id),('name', '=', widget_field_name)])
            rcs = request.env['rcs.address.field.mapping'].search([('model_id', '=', model.id),('widget_field_id','=',field_ids.id)])
            res={}
            if model and rcs:
                for data in rcs.line_ids:
                    res[data.label]= data.field_id.name
            else:
                return []

            if not result:
                return []
        return self.get_proper_address1(res ,widget_field_name,result)
