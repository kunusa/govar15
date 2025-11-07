# -*- coding: utf-8 -*-
{
    'name': "comisiones",
    'category': 'Sale',
    'version': '1.0',

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "OpenSolution",
    'website': "https://erp.opensolution.com.mx/",



    # any module necessary for this one to work correctly
    'depends': ['base','sale','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/scheduler_sequence.xml',
        'views/comisiones.xml',
        'views/res_user.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
