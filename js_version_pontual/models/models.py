# -*- coding: utf-8 -*-

from odoo import models, fields, api


class js_version_pontual(models.Model):
    _name = 'js_version_pontual.js_version_pontual'
    _description = 'js_version_pontual.js_version_pontual'

    version = fields.Char()
    create_date = fields.Datetime(readonly=True)


