# -*- coding: utf-8 -*-

{
    'name': 'Voice Message In Odoo',
    'version': '0.1',
    'category': 'Discuss',
    'summary': 'Send voice message in Chatter.',
    'description': "This module provides an option to record voice and "
                   "send voice messages in Chatter.",
    'author': "My Company",
    'depends': ['base', 'mail'],
    'assets': {
        'web.assets_qweb': [
            '/voice_note_in_chatter/static/src/xml/voice_in_odoo.xml',
        ],
        'web.assets_backend': [
            'voice_note_in_chatter/static/src/js/record_voice_component.js',
            'voice_note_in_chatter/static/src/js/voice_in_odoo.js',
            'voice_note_in_chatter/static/src/js/record_voice_model.js',
            'voice_note_in_chatter/static/src/js/attachment_card.js',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
