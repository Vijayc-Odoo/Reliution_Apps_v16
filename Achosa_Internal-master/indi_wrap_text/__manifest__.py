# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Wrap Text',
    'summary': 'Web',
    'version': '15.0.0.1',
    'description': """Add List View Wrap Text""",
    'depends': ['base', 'web', 'website'],
    'data': [
        # 'views/web_template_views.xml',
    ],
    'qweb': [
    ],
    'assets': {
        'web.assets_backend': [
            '/indi_wrap_text/static/src/scss/wrap_text_list_view.scss',
        ],
        'web.assets_frontend': [

        ],
        'web._assets_helpers': [
            '/indi_wrap_text/static/src/scss/wrap_text_utils.scss'
        ],
    },
    'installable': True,
    'auto_install': False,
    'bootstrap': True,
    'license': 'OPL-1',
}
