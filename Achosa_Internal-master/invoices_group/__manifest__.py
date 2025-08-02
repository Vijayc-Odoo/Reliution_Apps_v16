# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Invoices Group',
    'version' : '15.0.0.1',
    'summary': 'Permissions giving to the specific users.',
    'sequence': 10,
    'description': """
        This module provide the facility giving to permission of create the records such as 
        (Invoices, Delivery, etc...) to the specific users.
    """,
    'category': 'Sales/Sales',
    'website': '',
    'images' : [],
    'depends' : ['sale'],
    'data': [
        'security/invoices_group_security.xml',
        'views/sale_order_views.xml',
    ],
    'demo': [
        
    ],
    'qweb': [
        
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}
