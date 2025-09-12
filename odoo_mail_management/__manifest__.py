{
    'name': 'Email Management in Odoo',
    'version': '18.0.1.0.0',
    'category': 'Productivity',
    'summary': 'This Module will help to manage all type of mails in Odoo',
    'description': """Email Management in Odoo is a comprehensive module that 
    enhances the email handling capabilities of Odoo.This module is designed 
    to streamline and improve the management of all types of emails, providing
    a user-friendly interface and additional functionalities for increased
    productivity.""",
    'author': '',
    'company': '',
    'maintainer': '',
    'website': '',
    'depends': ['mail', 'calendar', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_icon_data.xml',
        'views/res_config_views.xml',
        'views/odoo_mail_views.xml',
        'views/mail_attachment_views.xml',
        'views/mail_message_views.xml',
        'views/fetch_incoming_mail_views.xml',
        'views/fetchmail_server_view.xml',
        'wizard/mail_specific_date.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "odoo_mail_management/static/src/css/main.css",
            "odoo_mail_management/static/src/js/*",
            "odoo_mail_management/static/src/xml/*",
        ]},
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
