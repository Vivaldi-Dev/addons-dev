# -*- coding: utf-8 -*-
{
    'name': "relatorio",

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
    'depends': ['base', 'website'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/template/table.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],



    'assets': {
        'web.assets_qweb': [
            'relatorio/static/src/js/js_template.xml',
        ],
        'web.assets_backend': [
            'relatorio/static/src/js/js_template.xml',
            'relatorio/static/src/js/public_widget.js'
        ],
        'web.assets_frontend': [
            'relatorio/static/src/js/js_template.xml',
            'relatorio/static/src/js/public_widget.js'
        ],
    },
}
