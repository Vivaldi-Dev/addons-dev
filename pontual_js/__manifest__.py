# -*- coding: utf-8 -*-
{
    'name': "pontual_js",

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
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'qweb': [
        '/pontual_js/static/src/xml/pontual_xml.xml',

    ],
    'assets': {
        'web.assets_backend': [
            '/pontual_js/static/src/js/pontual_js.js',
            # 'https://cdn.jsdelivr.net/npm/chart.js',
        ],
        'web.assets_qweb': [
            '/pontual_js/static/src/xml/pontual_xml.xml',
        ],
    },
}
