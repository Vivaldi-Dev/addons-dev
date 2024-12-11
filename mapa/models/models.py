from odoo import models, fields, api
from datetime import datetime, timedelta
from collections import defaultdict


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    mapa_id = fields.Many2one('mapa.mapa', string='Folha de Pagamento')


class Mapa(models.Model):
    _name = 'mapa.mapa'
    _description = 'Mapa de Folha de Pagamento'

    name = fields.Char(string='Descrição')
    month = fields.Selection(
        [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'),
         ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'),
         ('11', 'November'), ('12', 'December')],
        string='Month',
        required=True,
        help='Month related to the payroll'
    )

    payslip_ids = fields.One2many(
        comodel_name='hr.payslip',
        inverse_name='mapa_id',
        string='Payslips'
    )

    salary_rule_line_ids = fields.One2many(
        comodel_name='hr.payslip.line',
        string='Detalhes de Regra Salarial',
        compute='_compute_salary_rule_line_ids'
    )

    aggregated_salary_rule_lines = fields.One2many(
        comodel_name='folha.aggregated',
        inverse_name='mapa_id',
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

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        copy=False,
        help="Company",
        default=lambda self: self.env['res.company']._company_default_get()
    )

    def action_mapa_report(self):
        print("ID do registro:", self.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'irps',
            'params': {
                'id': self.id,
            },
            'context': {
                'params': {
                    'id': self.id,
                }
            },
        }

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        company_id = self.env.company.id
        if company_id:
            args = args or []
            args.append(('company_id', '=', company_id))
        print(f"Empresa ativa no search: {company_id}, Filtros aplicados: {args}")
        return super(Mapa, self).search(args, offset=offset, limit=limit, order=order, count=count)

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
            line_ids = record.payslip_ids.mapped('line_ids')
            record.salary_rule_line_ids = line_ids

    @api.depends('salary_rule_line_ids')
    def _compute_aggregated_salary_rule_lines(self):
        AggregatedLine = self.env['folha.aggregated']
        for record in self:

            if not record.id:
                record.flush(['id'])


            record.aggregated_salary_rule_lines.unlink()

            # Agrupa os dados
            aggregated_lines = []
            group_by_employee_contract = defaultdict(lambda: {'codes': {}, 'total': 0.0, 'job_position': None})

            for line in record.salary_rule_line_ids:
                key = (line.employee_id.id, line.contract_id.id, line.employee_id.x_nuit,
                       line.employee_id.x_inss, line.employee_id.barcode)

                group_by_employee_contract[key]['employee_id'] = line.employee_id.id
                group_by_employee_contract[key]['x_nuit'] = line.employee_id.x_nuit
                group_by_employee_contract[key]['x_inss'] = line.employee_id.x_inss
                group_by_employee_contract[key]['barcode'] = line.employee_id.barcode
                group_by_employee_contract[key]['codes'][line.code] = line.amount

            # Cria as linhas agregadas
            for key, values in group_by_employee_contract.items():
                aggregated_line = AggregatedLine.create({
                    'mapa_id': record.id,
                    'employee_id': values['employee_id'],
                    'irps_amout': values['codes'].get('IRPS', 0.0),
                    'numero_contribuinte': values['x_nuit'],
                    'numero_beneficiario': values['x_inss'],
                    'codigo_funcionario': values['barcode'],
                })

                aggregated_lines.append(aggregated_line.id)


class AggregatedLine(models.Model):
    _name = 'folha.aggregated'
    _description = 'Linha Agregada de Salário'

    mapa_id = fields.Many2one(
        'mapa.mapa',
        string='Mapa de IRPS',
        ondelete='cascade',
    )
    codigo_funcionario = fields.Char(string='Código do Funcionário')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    numero_contribuinte = fields.Char(string='Nº de Contribuinte')
    numero_beneficiario = fields.Char(string='Nº de Beneficiário')
    irps_amout = fields.Float(string='IRPS')
    valor = fields.Float(string='Valor')
