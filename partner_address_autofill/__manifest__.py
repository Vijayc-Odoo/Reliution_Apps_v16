# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

{
    "name": "Partner Address Auto Fill",
    "version": "18.0.0.1",
    "summary": "Paymob is the leading financial services enabler in the MENA-P region.",
    "depends": [
        'base',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/rcs_address_field_mapping_view.xml',
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'data/rcs_address.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'partner_address_autofill/static/src/js/rcs_address_auto_fill.js',
            'partner_address_autofill/static/src/xml/rcs_partner_address_google_place_dropdown.xml',
            'partner_address_autofill/static/src/js/rcs_form_controller.js',
        ],
        'web.assets_qweb': [
            'partner_address_autofill/static/src/xml/rcs_partner_address_google_place_dropdown.xml'
        ]
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
