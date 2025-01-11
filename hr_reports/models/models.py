# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    hrreport_id = fields.Many2one('hr_reports.hr_reports')


class hr_reports(models.Model):
    _name = 'hr_reports.hr_reports'
    _description = 'hr_reports.hr_reports'

    description = fields.Text()

    month = fields.Selection(
        [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'),
         ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'),
         ('11', 'November'), ('12', 'December')],
        string='Month',
        required=True,
        help='Month related to the payroll'
    )

    year = fields.Selection(
        [(str(year), str(year)) for year in range(2015, datetime.now().year + 2)],
        string='Ano',
        default=str(datetime.now().year),
        help='Ano relacionado ao pagamento'
    )


    payslip_ids = fields.One2many(
        comodel_name='hr.payslip',
        inverse_name='hrreport_id',
        string='Payslips',
        store=True
    )

    salary_rule_line_ids = fields.One2many(
        comodel_name='hr.payslip.line',
        string='Detalhes de Regra Salarial',
        compute='_compute_salary_rule_line_ids'
    )

    aggregated_salary_rule_lines = fields.One2many(
        comodel_name='folhapagamento.aggregated.line',
        inverse_name='hrreport_id',
        string='Linhas Agregadas',
        compute='_compute_aggregated_salary_rule_lines',
        store=True
    )

    state = fields.Selection(
        [('submitted', 'Submetido'),
         ('approved', 'Aprovado'),
         ('completed', 'Concluído'),
         ('cancelled', 'Cancelado')],
        string='Estado',
        default='submitted',
        required=True
    )

    departamento_id = fields.Many2one('hr.department', string='Departamento de RH')
    aprovado_por = fields.Many2one('res.users', string='Aprovado Por')

    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False, help="Company",
                                 default=lambda self: self.env['res.company']._company_default_get())
