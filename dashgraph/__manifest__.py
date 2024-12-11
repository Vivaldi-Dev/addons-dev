# -*- coding: utf-8 -*-
{
    'name': "dashgraph",

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

    'depends': ['base', 'web', 'sale', 'board'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],

    'assets': {
        'web.assets_qweb': [
            'dashgraph/static/src/components/sales_dashboard.xml',
            'dashgraph/static/src/components/kpi_card/kpi_card.xml'
        ],
        'web.assets_backend': [
            'dashgraph/static/src/components/sales_dashboard.xml',
            'dashgraph/static/src/components/sales_dashboard.js',
            'dashgraph/static/src/components/kpi_card/kpi_card.js',
            'dashgraph/static/src/components/kpi_card/kpi_card.xml',

        ],
    },
}
