from odoo import models, fields, api
from datetime import datetime, timedelta
from collections import defaultdict


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    mapairps_id = fields.Many2one('mapairps.mapairps', string='Mapa de IRPS')


class Mapairps(models.Model):
    _name = 'mapairps.mapairps'
    _description = 'Modelo para Mapairps'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        copy=False,
        help="Company",
        default=lambda self: self.env.company
    )

    month = fields.Selection(
        [
            ('01', 'January'), ('02', 'February'), ('03', 'March'),
            ('04', 'April'), ('05', 'May'), ('06', 'June'),
            ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')
        ],
        string='Month',
        required=True,
        help='Month related to the payroll'
    )

    payslip_ids = fields.One2many(
        comodel_name='hr.payslip',
        inverse_name='mapairps_id',
        string='Payslips'
    )

    salary_rule_line_ids = fields.Many2many(
        comodel_name='hr.payslip.line',
        compute='_compute_salary_rule_line_ids',
        string='Detalhes de Regra Salarial',
        store=True  # Garanta que o valor seja armazenado
    )

    aggregated_salary_rule_lines = fields.One2many(
        comodel_name='funcionario.model',
        inverse_name='mapairps_id',
        string='Linhas Agregadas',
        compute='_compute_aggregated_salary_rule_lines',
        store=True  # Garanta que o valor seja armazenado
    )

    @api.onchange('month')
    def _onchange_month(self):
        if self.month:
            year = datetime.now().year
            date_from = datetime.strptime(f'{year}-{self.month}-01', '%Y-%m-%d').date()
            date_to = (date_from.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            payslips = self.env['hr.payslip'].search([
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
            ])
            self.payslip_ids = [(6, 0, payslips.ids)]

    @api.depends('payslip_ids')
    def _compute_salary_rule_line_ids(self):
        for record in self:
            if record.payslip_ids:
                line_ids = record.payslip_ids.mapped('line_ids')
                record.salary_rule_line_ids = [(6, 0, line_ids.ids)]
                print(f"Salary Line IDs Computed: {line_ids.ids}")
            else:
                record.salary_rule_line_ids = [(5,)]
                print('nada bro')

    @api.depends('salary_rule_line_ids')
    def _compute_aggregated_salary_rule_lines(self):
        AggregatedLine = self.env['funcionario.model']
        for record in self:
            # Limpar registros antigos
            record.aggregated_salary_rule_lines.unlink()

            aggregated_lines = []
            group_by_employee_contract = defaultdict(
                lambda: {'codes': {}, 'total': 0.0, 'job_position': None, 'nuit': None})

            # Agrupar as linhas por employee_id, contract_id, nuit, inss e barcode
            for line in record.salary_rule_line_ids:
                key = (line.employee_id.id, line.contract_id.id, line.employee_id.x_nuit,
                       line.employee_id.x_inss, line.employee_id.barcode)

                group_by_employee_contract[key]['employee_id'] = line.employee_id.id
                group_by_employee_contract[key]['x_nuit'] = line.employee_id.x_nuit
                group_by_employee_contract[key]['x_inss'] = line.employee_id.x_inss
                group_by_employee_contract[key]['barcode'] = line.employee_id.barcode
                group_by_employee_contract[key]['codes'][line.code] = line.amount

            # Criar as linhas agregadas
            for key, values in group_by_employee_contract.items():
                irps_amount = values['codes'].get('IRPS', 0.0)
                if irps_amount < 0:
                    irps_amount = -irps_amount

                aggregated_line = AggregatedLine.sudo().create({
                    'mapairps_id': record.id,
                    'employee_id': values['employee_id'],
                    'irps_amout': irps_amount,
                    'numero_contribuinte': values['x_nuit'],
                    'numero_beneficiario': values['x_inss'],
                    'codigo_funcionario': values['barcode'],
                })

                aggregated_lines.append(aggregated_line.id)


class Funcionario(models.Model):
    _name = 'funcionario.model'
    _description = 'Modelo de Funcionário'

    mapairps_id = fields.Many2one(
        'mapairps.mapairps',
        string='Mapa de IRPS',
        ondelete='cascade'
    )

    codigo_funcionario = fields.Char(string='Código do Funcionário')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    numero_contribuinte = fields.Char(string='Nº de Contribuinte')
    numero_beneficiario = fields.Char(string='Nº de Beneficiário')
    irps_amout = fields.Float(string='IRPS')
    valor = fields.Float(string='Valor')


class Employee(models.Model):
    _inherit = 'hr.employee'

    x_nuit = fields.Char(string='Nuit')
    x_inss = fields.Char(string='INSS')
