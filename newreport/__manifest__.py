# -*- coding: utf-8 -*-
{
    'name': "newreport",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/assets.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'qweb': [
        '/newreport/static/src/xml/tableTemplate.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/newreport/static/src/js/report.js',
        ],
        'web.assets_qweb': [
            '/newreport/static/src/xml/tableTemplate.xml',
        ],
    },
}
