# -*- coding: utf-8 -*-
{
    'name': "Custom Returns - Devoluciones de Clientes",
    'summary': "Sistema de reclamos y devoluciones para clientes",
    'description': """
        Sistema completo de reclamos y devoluciones que permite a los clientes:
        - Buscar facturas por número
        - Crear reclamos de productos
        - Subir archivos adjuntos
        - Consultar el estado de sus reclamos
        - Integración con website_support
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website','website_support','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_claim.xml',
        'views/sequence_claim.xml',
        'views/claim_view.xml',
        'views/claim_wizard.xml',
        'views/website_settings.xml',
        'views/website_support_ticket_tree_inherit.xml',
        'views/search_invoice.xml',
        'views/form_claim.xml',
        'views/form_sent.xml',
        'views/info_claim.xml',
        'views/invoice_info_form.xml',
        'views/update_file.xml',
        'views/menu_website.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
}
