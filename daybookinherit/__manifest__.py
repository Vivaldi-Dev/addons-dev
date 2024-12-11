# -*- coding: utf-8 -*-
{
    'name': "daybookinherit",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'base_accounting_kit'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/views.xml',
        'report/daybook.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'daybookinherit/static/src/css/report.css',
            'daybookinherit/static/src/js/daybook.js',
            'daybookinherit/static/src/js/initial_balance.js',
        ],
        'web.assets_qweb': [
            'daybookinherit/static/src/xml/daybook.xml',

        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
