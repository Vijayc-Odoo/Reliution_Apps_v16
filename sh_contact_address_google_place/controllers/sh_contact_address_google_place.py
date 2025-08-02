# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
import requests

from odoo import http
from odoo.http import request
from odoo.tools import html2plaintext
from odoo.osv.expression import AND

GOOGLE_MAP_PLACES = 'https://maps.googleapis.com/maps/api/place'
# GOOGLE_MAP_PLACES = 'https://places.googleapis.com/v1/places:'

MAPPING_GOOGLE_FIELDS = {
    'country': ['country'],
    'street_number': ['number'],
    'neighborhood': [''],
    'locality': ['city'],
    'route': ['street'],
    'postal_code': ['zip'],
    'administrative_area_level_1': ['state', 'city'],
    'administrative_area_level_2': ['state', 'country']
}


class ShContactAddressGooglePlace(http.Controller):

    def _convert_to_standard_address(self, g_fields):
        """
        This function converts Google Maps API address fields to standard address fields in Odoo.

        :param g_fields: It is a list of dictionaries containing information about the address fields
        returned by the Google Maps API. Each dictionary represents a single address component, such as
        street number, city, state, etc. The dictionary contains keys such as 'long_name', 'short_name',
        and 'type', which provide information about
        :return: a dictionary containing the standard address values extracted from the input Google
        fields.
        """
        address_vals = {}

        for g_field in g_fields:
            fields_standard = MAPPING_GOOGLE_FIELDS[g_field['type']
                                                    ] if g_field['type'] in MAPPING_GOOGLE_FIELDS else []

            for s_field in fields_standard:
                if s_field in address_vals:
                    continue
                if s_field == 'country':
                    country = request.env['res.country'].search(
                        [('code', '=', g_field['short_name'].upper())], limit=1)
                    address_vals[s_field] = country.id if country else False
                    address_vals['country_code'] = country.code if country else False
                elif s_field == 'state':
                    domain = [('code', '=', g_field['short_name'].upper())]
                    if address_vals['country']:
                        domain = AND(
                            [domain, [('country_id.id', '=', address_vals['country'])]])
                    state = request.env['res.country.state'].search(domain)
                    if len(state) == 1:
                        address_vals[s_field] = state.id
                else:
                    address_vals[s_field] = g_field['long_name']
        return address_vals

    @http.route('/sh_find_on_gmap/address', type='json', auth='user')
    def sh_find_on_gmap_address(self, partial_address):
        """
        This function uses the Google Maps Places API to find addresses based on a partial address
        input.

        :param partial_address: partial_address is a string parameter that represents a partial address
        entered by the user. This parameter is used to search for matching addresses using the Google
        Places Autocomplete API
        :return: list of dictionaries containing the description and place_id of
        the results obtained from a Google Maps Places Autocomplete API call, based on a partial address
        provided as input. If the partial address is less than or equal to 5 characters, an empty list
        is returned. If the company associated with the user has enabled and provided a valid Google API
        key, the API call is made and the
        """
        if len(partial_address) <= 5:
            return []

        company = request.env.user.company_id or request.env.company
        if company and company.sh_is_enable_google_api_key and company.sh_google_api_key:
            params = {
                'key': company.sh_google_api_key,
                'fields': 'formatted_address,name',
                'inputtype': 'textquery',
                'types': 'address',
                'input': partial_address
            }

            try:
                results = requests.get(
                    f'{GOOGLE_MAP_PLACES}/autocomplete/json', params=params, timeout=2.5).json()
                print(results)
            except (TimeoutError, ValueError):
                return {"results": []}

            results = results.get('predictions', [])

            return [{'description': result['description'],
                     'place_id': result['place_id']
                     } for result in results]
        return []

    @http.route('/sh_find_on_gmap/fill_address', type='json', auth='user')
    def sh_find_on_gmap_address_full(self, address, place_id):
        """
        This function uses the Google Maps API to retrieve and format a full address based on a given
        place ID and address input.

        :param address: The full address.
        :param place_id: The place_id parameter is a unique identifier for a specific place on Google
        Maps. It is used to retrieve detailed information about the place, such as its address
        components and formatted address
        :return: a dictionary containing the complete address details of a place identified by its
        place_id on Google Maps. The address details include fields such as street, city, state,
        country, zip, etc.
        """
        company = request.env.user.company_id or request.env.company
        if company and company.sh_is_enable_google_api_key and company.sh_google_api_key:
            params = {
                'key':  company.sh_google_api_key,
                'place_id': place_id,
                'fields': 'address_component,adr_address'
            }

            try:
                results = requests.get(
                    f'{GOOGLE_MAP_PLACES}/details/json', params=params, timeout=2.5).json()
                html_address = results['result']['adr_address']
                results = results['result']['address_components']

                for res in results:
                    res['type'] = res.pop('types')[0]

            except (TimeoutError, ValueError):
                return []

            sequence = list(MAPPING_GOOGLE_FIELDS.keys())
            results.sort(key=lambda result: sequence.index(
                result['type']) if result['type'] in sequence else 143)

            complete_address = self._convert_to_standard_address(results)

            if 'number' not in complete_address:
                house_number = address.replace(complete_address.get('zip', ''), '').replace(
                    complete_address.get('street', ''), '').replace(complete_address.get('city', ''), '')
                complete_address['number'] = house_number.split(',')[0].strip()
                complete_address[
                    'formatted_street'] = f'{complete_address["number"]} {complete_address.get("street", "")}'
            else:
                html2street = html2plaintext(html_address.split(',')[0])
                street = f'{complete_address["number"]} {complete_address.get("street", "")}'
                complete_address['formatted_street'] = html2street if len(
                    html2street) >= len(street) else street
        
                
            return complete_address
