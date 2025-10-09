# -*- coding: utf-8 -*-
{
    'name': "customs_govar",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'stock', 'purchase', 'remisiones', 'account'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/denied_product.xml',
        'views/warehouse.xml',
        'views/account_move.xml',
        'views/label_wizard.xml',
        'views/res_company.xml',
        'views/settings_inventory.xml',
        'views/settings_accounting.xml',
        'views/sale_order.xml',
        'views/res_partner.xml',
        'views/email_template.xml',
        'views/product_avaibility.xml',
        'views/wizard_cfdi.xml',
        'views/purchase.xml',
        'views/stock.xml',
        'views/product.xml',
        'report/label_invoice.xml',
        'report/label_remision.xml',
        'report/report_overdue.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
