# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Employee(models.Model):
    _inherit = 'hr.employee'

    x_nuit = fields.Char(string='Nuit')
    x_inss = fields.Char(string='INSS')
    x_ativo = fields.Boolean(string='Notificação em Tempo Real', default=False)


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    leave_type = fields.Selection([
        ('admissao', 'Admissão'),
        ('demissao', 'Demissão'),
        ('retorno', 'Retorno'),
        ('licenca_maternidade', 'Licença de Maternidade'),
        ('acidente_trabalho', 'Acidente de Trabalho'),
        ('servico_militar', 'Serviço Militar Obrigatório'),
        ('doenca_profissional', 'Doença Profissional'),
        ('doenca_pessoal', 'Doença Pessoal'),
        ('falecimento', 'Falecimento'),
        ('falta', 'Falta'),
        ('subtrativa', 'Subtrativa')
    ], string="Tipo de Licença",  default='admissao')

class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    holiday_status_id = fields.Many2one(
        "hr.leave.type", compute='_compute_from_employee_id', store=True, string="Time Off Type", required=True,
        readonly=False,
        states={'cancel': [('readonly', True)], 'refuse': [('readonly', True)], 'validate1': [('readonly', True)],
                'validate': [('readonly', True)]},
        domain=[])


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company.id,
        required=True,
    )

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        company_id = self.env.company.id
        if company_id:
            args = args or []
            args.append(('company_id', '=', company_id))

        return super(HrPayslipRun, self).search(args, offset=offset, limit=limit, order=order, count=count)