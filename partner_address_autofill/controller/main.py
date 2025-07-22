# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

import requests
from odoo.http import request
from odoo import http, fields
from odoo.exceptions import ValidationError

URL = 'https://places.googleapis.com/v1/places'

class RcsContactAddressGooglePlace(http.Controller):

    def get_proper_address(self, fields_key, result):
        '''

        :param fields_key: A dictionary where the key is a label (e.g., 'STREET') and the value is the corresponding technical field name to store the custom address data.
        :param result: A JSON response from the Google Maps API containing address components.
               Example keys include 'name', 'id', 'formattedAddress', 'addressComponents', and 'displayName'.
        :return: A dictionary where the key is a technical field name and the value is the corresponding address value.
        '''
        data = {
            'street': '', 'street2': '', 'city': '', 'zip': '',
            'state_name': '', 'state_code': '', 'country_name': '', 'country_code': ''
        }

        display_name = result.get('displayName', {})
        if display_name.get('text'):
            data['street'] = display_name['text']

        address_components=result.get('addressComponents')
        for res in address_components:
            type = res.get('types', [''])[0]
            long = res.get('longText', '')
            short = res.get('shortText', '')

            if type == 'route':
                data['street'] += (", " if data['street'] else "") + long
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
            # if type == 'neighborhood':
            #     data['street'] += (", " if data['street'] else "") + long
            if type == 'neighborhood' or type == 'sublocality_level_1' or type == 'sublocality_level_2':
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

    # This method is used to request and search for places.
    @http.route('/res_find_gmap/address', type='json', auth='user')
    def rcs_find_gmap_address(self, partial_address):
        '''

        :param partial_address: The characters entered by the user to search for an address.
        :return: A list of place names to display to the user, along with their corresponding place IDs for easy retrieval of detailed address information.

        '''
        company = request.env.user.company_id or request.env.company

        # Check minimum characters required to trigger search
        if not partial_address or len(partial_address) < company.rcs_google_api_search_char:
            return []

        # Determine region code restriction
        country_codes = company.rcs_google_country.mapped('code') if company.rcs_google_country else []

        # Validate API access
        if not (company.rcs_is_enable_google_api_key and company.rcs_google_api_key):
            return []

        # Prepare headers and payload
        headers = {
            'X-Goog-Api-Key': company.rcs_google_api_key,
            'Content-Type': 'application/json',
            'X-Goog-FieldMask': 'suggestions.placePrediction.text.text,suggestions.placePrediction.placeId'
        }

        payload = {
            'input': partial_address,
            'includedRegionCodes':country_codes or ""
        }

        # Make request to Google API
        response = requests.post(f'{URL}:autocomplete', headers=headers, json=payload)
        if response.status_code != 200:
            return []

        result = response.json()
        results = result.get('suggestions')
        if not results:
            print("Not Result Found")
            return []

        # Extract and return suggestions
        return [
            {
                'placeName': res.get('placePrediction').get('text').get('text'),
                'id': res.get('placePrediction').get('placeId')
            } for res in results if res.get('placePrediction')]


    # This method is used to fetch and process address details by making a request using the Place ID.
    @http.route("/rcs_detail_gmap/address", type='json', auth='user')
    def rcs_fill_gmap_address(self, address, place_id,resModel,widget_field_name):
        '''

        :param address: The formatted address entered by the user.
        :param place_id: The Place ID used to accurately retrieve place details.
        :param resModel: The model in which the widget field is defined.
        :param widget_field_name: The name of the field where the widget is applied.
        :return: A dictionary containing the address data and the corresponding fields to store it.

        '''
        company = request.env.user.company_id or request.env.company

        # Validate company API access
        if not (company and company.rcs_is_enable_google_api_key and company.rcs_google_api_key):
            return []

        # Prepare API headers
        headers = {
            'X-Goog-Api-Key': company.rcs_google_api_key,
            'Content-Type': 'application/json',
            'X-Goog-FieldMask': 'id,name,displayName,formattedAddress,addressComponents',
        }

        # Call Google API
        response = requests.get(f'{URL}/{place_id}', headers=headers)
        result = response.json()

        if not result:
            return []

        # Get model and field mapping
        model = request.env['ir.model'].search([('model', '=', resModel)], limit=1)
        if not model:
            return []

        field = request.env['ir.model.fields'].search([
            ('model_id', '=', model.id),
            ('name', '=', widget_field_name)
        ], limit=1)

        if not field:
            return []

        mapping = request.env['rcs.address.field.mapping'].search([
            ('model_id', '=', model.id),
            ('widget_field_id', '=', field.id)
        ], limit=1)

        if not mapping:
            return []
        res = {}
        if model and model:
            for data in mapping.line_ids:
                res[data.label] = data.field_id.name

        # Return processed address
        return self.get_proper_address(res, result)
