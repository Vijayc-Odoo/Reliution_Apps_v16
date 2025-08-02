# -*- coding: utf-8 -*-
{
    'name': "Dynamic Backend Theme UI",
    'version': '15.0.0.1',
    'sequence': 1,
    'website': "https://cronquotech.odoo.com",
    'summary': '''Color change theme,
        theme, theme color, Dynamic theme Color,
        theme change,
        multi, multi color,
        multi color theme,
        them multi color, change color,Dynamic Backend Theme Color,
        Dynamic,
        Color, Backend Theme,
        Backend,
           ''',
    'description': "Using this module user able to set color in settings",
    'author': 'CRON QUOTECH',
    'category': 'Theme',
    'depends': ['base', 'web', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/dynamic_colors_views.xml',
    ],
    'images': [
        'static/description/banner.png', 'static/description/cronquotech_banner_screenshot.png'
    ],
    'qweb': [
    ],
    'assets': {
        'web.assets_backend': [
            '/dynamic_backend_ui_cqt/static/src/scss/colors.scss'
        ],
        'web.assets_common': [

        ],
        'web.assets_frontend': [

        ],
    },
    "support": "cronquotech@gmail.com",
    "license": "LGPL-3",
    'price': 9.00,
    'currency': 'USD',
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': '_post_init_hook',
}
