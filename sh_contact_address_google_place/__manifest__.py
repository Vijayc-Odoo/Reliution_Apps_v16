# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

{
    'name': 'Partner Address Autofill | Customer Address Autofill | Contact Address Autofill',
    'author': 'Softhealer Technologies',
    'website': 'https://www.softhealer.com',
    'support': 'support@softhealer.com',
    'category': 'Human Resources',
    'license': 'OPL-1',
    'summary': "AutoFill Of Address Google places API Customer Address Auto Fill Based On Google Places Address Autofill Based On Google Places Auto Fill Street Auto Fill PIN Auto Fill Country Contact Address Auto Fill State Company Address Auto Fill Odoo",
    'description': """This module allows to auto fill company address quickly. Once you configure google API key it auto fill address like street number, city, zip code, country & state.""",
    'version': '15.0.3',
    'depends': ['contacts'],
    'application': True,
    'data': [
        "views/res_company_views.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml"
    ],
    'assets': {
        'web.assets_backend': {
            'sh_contact_address_google_place/static/src/js/sh_address_auto_complete.js',
            'sh_contact_address_google_place/static/src/scss/sh_address_auto_complete.scss',
        },
        'web.assets_qweb': [
            'sh_contact_address_google_place/static/src/xml/sh_contact_address_google_place_dropdown.xml'
        ]
    },
    'auto_install': False,
    'installable': True,
    "images": ["static/description/background.png", ],
    'price': 25,
    'currency': 'EUR',
}
