# -*- coding: utf-8 -*-

{
    'name': 'Past Transaction Data',
    'category': 'Accounting',
    'summary': 'Past Transaction Data',
    'version': '15.0.0.1',
    'description': """Authorize.Net Payment Acquirer""",
    'depends': ['base', 'mail', 'contacts', 'payment_authorize'],
    'data': [
        'security/ir.model.access.csv',
        'data/missed_transaction_data.xml',
        'views/payment_transaction_audit.xml',
    ],
    'installable': True,
    'license': 'OPL-1',
}
