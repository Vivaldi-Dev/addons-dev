# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Employee(models.Model):
    _inherit = 'hr.employee'

    x_ativo = fields.Boolean(string='Notificação em Tempo Real', default=False)


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    code = fields.Char(string='Code')


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    holiday_status_id = fields.Many2one(
        "hr.leave.type", compute='_compute_from_employee_id', store=True, string="Time Off Type", required=True,
        readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)],
                'validate': [('readonly', True)]},
        domain=[])