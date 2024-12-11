# -*- coding: utf-8 -*-
{
    'name': "dash_avaliacao",

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
    'depends': ['base','web', 'sale', 'board'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',

    ],

    'assets': {
        'web.assets_qweb': [
            'dash_avaliacao/static/src/xml/template.xml',
            'dash_avaliacao/static/src/xml/dash_template.xml',


        ],
        'web.assets_backend': [
            'dash_avaliacao/static/src/css/lib/dashboard.css',
            'dash_avaliacao/static/src/css/style.scss',
            'dash_avaliacao/static/src/js/totalrequisition.js',
            'dash_avaliacao/static/src/js/dashboard.js'

        ]
    },

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
