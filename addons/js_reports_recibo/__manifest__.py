# -*- coding: utf-8 -*-
{
    'name': "js_reports_recibo",

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

    'depends': ['base', 'hr', 'hr_payroll_community', 'web', 'folhapagamento'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/report.xml',
        'report/template/recibo.xml',
        'report/template/insstxt.xml',
        'report/template/inssreport.xml',
        'report/template/irps.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
