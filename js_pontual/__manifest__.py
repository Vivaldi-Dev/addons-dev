# -*- coding: utf-8 -*-
{
    'name': "js_pontual",

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

    'depends': ['base','web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],

    'demo': [
        'demo/demo.xml',
    ],

    'qweb': [
        '/js_pontual/static/src/xml/pontual_reporte.xml',
        '/js_pontual/static/src/xml/relatorio.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/js_pontual/static/src/js/pontul_report.js',
            'https://cdn.jsdelivr.net/npm/chart.js',
        ],
        'web.assets_qweb': [
            '/js_pontual/static/src/xml/pontual_reporte.xml',
            '/js_pontual/static/src/xml/relatorio.xml'
        ],
    },

}
