# -*- coding: utf-8 -*-
{
    'name': "jsreport",

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

    'depends': ['base', 'web','account'],

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
        '/jsreport/static/src/xml/reporttemplate.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/jsreport/static/src/js/report.js',
        ],
        'web.assets_qweb': [
            '/jsreport/static/src/xml/reporttemplate.xml',
        ],
    },

}
