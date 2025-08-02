# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale Subscription',
    'summary': 'Subscriptions',
    'version': '15.0.0.1',
    'description': """Add Cancel Button in Subscription""",
    'depends': ['achosa'],
    'data': [
        'views/sale_subscription_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'OPL-1',
}
