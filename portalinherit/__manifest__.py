
# -*- coding: utf-8 -*-
{
    'name': 'portalinherit',
    'description': 'Default website theme',
    'category': 'Theme',
    'sequence': 40,
    'version': '1.0',
    'depends': ['website','portal', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/portal_template.xml',
        'views/templates.xml',
        'views/tempates/Dashboard.xml',
        'views/tempates/Dashboardv2.xml',
        'security/security_accessvol.xml',
        'views/page.xml',
        'views/tempates/menunav.xml',
        'views/portalHide.xml',
        'views/assets.xml',

    ],
    'qweb': [
    ],

    'assets': {
        'web.assets_frontend': ['/portalinherit/static/src/js/js.js',],
    },

    'images': [

    ],
    'snippet_lists': {
    },
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
