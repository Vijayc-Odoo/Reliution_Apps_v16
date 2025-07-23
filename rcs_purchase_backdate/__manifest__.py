# -*- coding: utf-8 -*-
# Part of Reliution Consulting Services.

{
    "name": "RCS Purchase Backdate ",
    "author": "Reliution Consulting Services.",
    "version": "0.0.1",
    "depends": ["purchase", "stock","purchase_stock"],
    "data": [
        'security/ir.model.access.csv',
        'security/rcs_purchase_backdate_groups.xml',
        'data/purchase_order_data.xml',
        'wizard/rcs_purchase_backdate_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_views.xml',
        'views/stock_move_line_views.xml',
    ],

    "auto_install": False,
    "installable": True,
    "application": True,
    # "images": ["static/description/background.png", ],
    "license": "OPL-1",
    # "price": 20,
    "currency": "EUR"
}
