# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Address Autocomplete - Google API',
    'version': '15.0.0.1',
    'summary': '',
    'sequence': 10,
    'description': """
        Address Autocomplete using Google API
    """,
    'category': 'Extra Tools',
    'website': '',
    'images': [],
    'depends': ['achosa', 'web'],
    'data': [
        'data/address_autocomplete_data.xml',
        'views/gmap_templates.xml',
        'views/home_warranty_views.xml',
    ],
    'demo': [

    ],
    'qweb': [

    ],
    'assets': {
        'web.assets_backend': [
            '/address_autocomplete/static/src/js/address_autocomplete_fieldchar.js',
        ],
        'web.assets_frontend': [

        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': '',
    'license': 'OPL-1',
}
