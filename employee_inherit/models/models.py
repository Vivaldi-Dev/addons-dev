# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Employee(models.Model):
    _inherit = 'hr.employee'

    x_nuit = fields.Char(string='Nuit')
    x_inss = fields.Char(string='INSS')
    x_ativo = fields.Boolean(string='Notificação em Tempo Real', default=True)
