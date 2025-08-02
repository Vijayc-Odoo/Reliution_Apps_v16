# -*- coding: utf-8 -*-

{
    'name': 'Web Editor patch - Achosa',
    'version': '15.0.0.1',
    'sequence': 4,
    'category': 'Achosa',
    'summary': '',
    'description': """
      AO-985: fix Email editor freezing page and not working  
    """,
    'author': "Restyn",
    'website': 'www.achosahw.com',
    'license': 'AGPL-3',
    'depends': ['base','web_editor'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'web_editor_patch/static/src/js/backend/field_html2.js',
        ],
    },
    'auto_install': True,
    'installable': True,
    'active': False,
}