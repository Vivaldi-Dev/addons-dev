# -*- coding: utf-8 -*-
{
    'name': "dashboard_pontual",

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
    'depends': ['base','hr','hr_attendance','website_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'qweb': [
        '/dashboard_pontual/static/src/xml/dash_pontual.xml',
    ],

    'assets': {
        'web.assets_backend': [
            '/dashboard_pontual/static/src/js/dash_pontual.js',
            'https://cdn.jsdelivr.net/npm/chart.js',
        ],
        'web.assets_qweb': [
            '/dashboard_pontual/static/src/xml/dash_pontual.xml',
        ],
    },
}
