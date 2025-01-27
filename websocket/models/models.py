# -*- coding: utf-8 -*-

from odoo import models, fields, api


class websocket(models.Model):
    _name = 'websocket.websocket'
    _description = 'websocket.websocket'

    name = fields.Char()
    state = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], default='active')
    message = fields.Text()
    description = fields.Text()

