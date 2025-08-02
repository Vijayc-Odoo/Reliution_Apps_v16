# -*- coding: utf-8 -*-
#################################################################################
# Author      : Kanak Infosystems LLP. (<https://www.kanakinfosystems.com/>)
# Copyright(c): 2012-Present Kanak Infosystems LLP.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.kanakinfosystems.com/license>
#################################################################################
{
    'name': 'Paypal Backend Payment',
    'description': """
    Paypal Backend Payment
    """,
    'summary': 'This module enables backend payment using paypal',
    'category': 'Payment',
    'license': 'OPL-1',
    'author': 'Kanak Infosystems LLP.',
    'website': "https://www.kanakinfosystems.com",
    'images': ['static/description/banner.jpg'],
    'depends': ['sale', 'sale_management', 'sale_stock', 'account', 'payment', 'payment_paypal'],
    'data': [
        'views/payment_acquirer.xml',
        'views/sale_view.xml',
        'data/payment_paypal_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 50,
    'currency': 'EUR',
}
