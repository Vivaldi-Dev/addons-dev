from odoo import models, fields, api
from datetime import datetime, timedelta
from collections import defaultdict

class Payroll(models.Model):
    _inherit = 'hr.payslip'

    payroll_map_id = fields.Many2one('payroll.map', string='Folha de Pagamento')

class PayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    payroll_map_id = fields.Many2one(
        comodel_name='payroll.map',
        string='Folha de Pagamento',
        compute='_compute_payroll_map_id',
        store=True,
        readonly=False
    )

    @api.depends('slip_id', 'slip_id.payroll_map_id')
    def _compute_payroll_map_id(self):
        for line in self:
            line.payroll_map_id = line.slip_id.payroll_map_id



class PayrollMap(models.Model):
    _name = 'payroll.map'
    _description = 'Mapa de Folha de Pagamento'

    description = fields.Char(string='Descrição')
    period = fields.Selection(
        [('01', 'Janeiro'), ('02', 'Fevereiro'), ('03', 'Março'), ('04', 'Abril'), ('05', 'Maio'),
         ('06', 'Junho'), ('07', 'Julho'), ('08', 'Agosto'), ('09', 'Setembro'), ('10', 'Outubro'),
         ('11', 'Novembro'), ('12', 'Dezembro')],
        string='Mês',
        required=True,
        help='Mês referente à folha de pagamento'
    )

    payslips = fields.One2many(
        comodel_name='hr.payslip',
        inverse_name='payroll_map_id',
        string='Folhas de Pagamento'
    )

    salary_details = fields.One2many(
        comodel_name='hr.payslip.line',
        inverse_name='payroll_map_id',
        string='Detalhes de Regras Salariais',
        compute='_compute_salary_details',
        store=True,
    )

    aggregated_lines = fields.One2many(
        comodel_name='payroll.aggregated',
        inverse_name='payroll_map_id',
        string='Linhas Agregadas',
        compute='_compute_aggregated_lines',
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

    company = fields.Many2one('res.company', string='Empresa', readonly=True, copy=False, help="Empresa",
                              default=lambda self: self.env['res.company']._company_default_get())

    @api.model
    def create(self, vals):
        record = super(PayrollMap, self).create(vals)
        record._compute_aggregated_lines()
        return record

    def generate_payroll_report(self):
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
            args.append(('company', '=', company_id))
        print(f"Empresa ativa no search: {company_id}, Filtros aplicados: {args}")
        return super(PayrollMap, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.onchange('period')
    def _onchange_period(self):
        if self.period:
            year = datetime.now().year
            date_from = datetime.strptime(f'{year}-{self.period}-01', '%Y-%m-%d').date()
            date_to = (date_from.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            payslips = self.env['hr.payslip'].search([
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
            ])
            self.payslips = [(6, 0, payslips.ids)]

    @api.depends('payslips.line_ids')
    def _compute_salary_details(self):
        for record in self:
            record.salary_details = record.payslips.mapped('line_ids')

    @api.depends('salary_details')
    def _compute_aggregated_lines(self):
        for record in self:
            print(f"Procesando record ID: {record.id}")

            if not record.id:
                # Forzar persistencia si el ID no está disponible
                record.flush()

            # Limpiar líneas existentes
            record.aggregated_lines = [(5, 0, 0)]

            group_by_employee_contract = defaultdict(
                lambda: {'codes': {}, 'total': 0.0, 'job_position': None}
            )

            for line in record.salary_details:
                print(f"Procesando línea salarial: {line.id}")
                key = (line.employee_id.id, line.contract_id.id, line.employee_id.x_nuit,
                       line.employee_id.x_inss, line.employee_id.barcode)

                group_by_employee_contract[key]['employee_id'] = line.employee_id.id
                group_by_employee_contract[key]['x_nuit'] = line.employee_id.x_nuit
                group_by_employee_contract[key]['x_inss'] = line.employee_id.x_inss
                group_by_employee_contract[key]['barcode'] = line.employee_id.barcode
                group_by_employee_contract[key]['codes'][line.code] = line.amount

            aggregated_lines = []
            for key, values in group_by_employee_contract.items():
                inss_amount = values['codes'].get('INSS', 0.0)

                if inss_amount < 0:
                    inss_amount = -inss_amount

                if inss_amount <= 0:
                    print(f"INSS inválido para el empleado {values['employee_id']}: {inss_amount}")
                    continue

                aggregated_line = self.env['payroll.aggregated'].create({
                    'payroll_map_id': record.id,
                    'employee_id': values['employee_id'],
                    'inss_amout': inss_amount,
                    'numero_contribuinte': values['x_nuit'],
                    'numero_beneficiario': values['x_inss'],
                    'codigo_funcionario': values['barcode'],
                })
                print(f"Línea agregada creada con ID: {aggregated_line.id}")
                aggregated_lines.append(aggregated_line)

            # Asignar líneas creadas al registro
            record.aggregated_lines = [(4, line.id) for line in aggregated_lines]
            print(f"Líneas agregadas actualizadas para el record ID: {record.id}")


class AggregatedLine(models.Model):
    _name = 'payroll.aggregated'
    _description = 'Linha Agregada de Salário'

    payroll_map_id = fields.Many2one('payroll.map', string='Folha de Pagamento', ondelete='cascade')

    codigo_funcionario = fields.Char(string='Código do Funcionário')

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    numero_contribuinte = fields.Char(string='Nº de Contribuinte')
    numero_beneficiario = fields.Char(string='Nº de Beneficiário')
    inss_amout = fields.Float(string='INSS')
    valor = fields.Float(string='Valor')
