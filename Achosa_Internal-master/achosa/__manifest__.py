# -*- coding: utf-8 -*-
{
    'name': 'ACHOSA',
    'version': '15.0.2.0',
    'category': 'Studio',
    "sequence": 1,
    'website': 'https://achosa.odoo.com/',
    'description': u"""
ACHOSA Home Warranty System
===========================

APPS:
-----
 - Home Claims
 - Home Warranties

Written by Joe Shields for ACHOSA 9/21/2018

Last Production update:
""",
    'author': 'RESTYN',
    'depends': [
        'base',
        'crm',
        'account',
        'product',
        'sale',
        'sale_coupon',
        'sale_subscription',
        'hr_contract',
        'hr_expense',
        # 'website_form',
        'website_sale',
        'survey',
        'mail_bot',
    ],
    'data': [
        'security/claims_access.xml',
        'security/hw_access.xml',
        'security/sale_subscription_access.xml',
        'security/ir.model.access.csv',
        'security/vendor_zip_codes_access.xml',
        'security/mail_template_access_group.xml',
        'security/outgoing_mail_access_rights.xml',
        'wizard/sale_coupon_apply_code_views.xml',
        'wizard/home_warranty_email_views.xml',
        'wizard/update_property_data.xml',
        'wizard/receive_check.xml',
        'wizard/account_payment_register_views.xml',
        'views/claims_view.xml',
        'views/product_views.xml',
        'views/contact_views.xml',
        'views/res_country_state_views.xml',
        'views/res_partner_views.xml',
        # 'views/mail_compose_message_views.xml',
        'views/my_portal.xml',
        'views/Claim_report.xml',
        'views/HW_SO_Report.xml',
        'views/home_warranty_views.xml',
        'views/home_warranty_views_admin.xml',
        'views/home_warranty_portal_templates.xml',
        'views/invoice_views.xml',
        'views/sale_order_views.xml',
        'views/sale_subscription_template_view.xml',
        'views/sale_subscription_views.xml',
        'views/subscription_portal_templates.xml',
        'views/sale_coupon_views.xml',
        'views/crm_lead_views.xml',
        'views/website.xml',
        'views/payment.xml',
        'views/res_company_views.xml',
        'views/templates.xml',
        'views/product_pricelist_views.xml',
        'menu/claims_menu.xml',
        'menu/home_warranty_menu.xml',
        'data/CL_templates.xml',
        'data/HW_templates.xml',
        'data/terms.xml',
        'data/seq.xml',
        'data/achosa_email_template.xml',
        'data/ir_cron.xml',

    ],
        'assets': {
            'web.assets_backend': [
                'sale/static/src/js/variant_mixin.js',
                'achosa/static/src/js/achosa_widgets.js',
                'achosa/static/src/js/hw_hide_sections.js',
                'sale/static/src/js/variant_mixin.js',
            ],
            'web.assets_frontend': [
                'achosa/static/src/css/achosa_frontend_assets.css',
                'achosa/static/src/js/product_property_type.js',
            ],
            'web.assets_qweb': [
                'achosa/static/src/xml/achosa.xml',
                'achosa/static/src/xml/hide_generate_leads.xml',

        ],
        },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
}
