# -*- coding: utf-8 -*-
{
    'name': "folhapagamento",

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
    'category': 'folhapagamento',
    'version': '0.1',

    'depends': ['base', 'hr', 'hr_payroll_community','web',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'report/report.xml',
        'views/templates.xml',
        'report/templatereport.xml',
        'report/inss_report.xml',
        'report/irpsreport.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'qweb': [
        'folhapagamento/static/src/xml/reportemplat.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/folhapagamento/static/src/js/report.js',
        ],
        'web.assets_qweb': [
            'folhapagamento/static/src/xml/reportemplat.xml',
        ],
    },
}
