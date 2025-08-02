# -*- coding: utf-8 -*-
{
    'name': 'Renewal Terms Sales',
    'version': '15.0.0.1',
    'category': 'Sales',
    "sequence": 1,
    'website': 'https://achosa.odoo.com/',
    'description': u"""
ACHOSA Renewal Terms Sales
===========================

Last Production update:
""",
    'author': 'RESTYN',
    'depends': [
        'sale',
    ],
    'data': [
        'views/sale_portal_templates.xml',
    ],
    'qweb': [

        ],
    'installable': True,
    'auto_install': True,
    'application': True,
    'license': 'OPL-1',
}
