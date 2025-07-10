# -*- coding: utf-8 -*-
# Copyright (C) Reliution Consulting Services.

{
    "name": "Partner Address Auto Fill",
    "version": "18.0.0.1",
    # "category": "Accounting/Payment Providers",
    # "author": "",
    # "maintainer": "Paymob",
    # "website": "https://www.paymob.com",
    # "sequence": 350,
    "summary": "Paymob is the leading financial services enabler in the MENA-P region.",
    # "description": "Odoo plugin for paymob first fintech company to receive the Central Bank of Egypt’s (CBE) Payments Facilitator license in 2018. We launched operations in Pakistan in 2021 and in the UAE in 2022. Paymob received Saudi Payments PTSP certification in May 2023 enabling us to launch operations in KSA. In December 2023 Paymob became the first international fintech company to receive Oman’s PSP",
    "depends": [
        'base',
        "payment",
        "account",
        # "whatsapp_payment",
        # "whatsapp",
    ],
    "data": [
        'views/res_partner_views.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'partner_address_autofill/static/src/js/rcs_address_auto_fill.js',
            'partner_address_autofill/static/src/xml/rcs_partner_address_google_place_dropdown.xml',
        ],
        'web.assets_qweb': [
            'partner_address_autofill/static/src/xml/rcs_partner_address_google_place_dropdown.xml'
        ]
    },
    "installable": True,
    "application": True,
    # "images": ["static/description/banner.jpg"],
    # "post_init_hook": "post_init_hook",
    # "uninstall_hook": "uninstall_hook",
    "license": "LGPL-3",
}
