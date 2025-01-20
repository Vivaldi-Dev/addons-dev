from odoo import models, fields, api, exceptions, _
from datetime import datetime, timedelta
from collections import defaultdict
from odoo.exceptions import ValidationError, UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    folhapagamento_id = fields.Many2one('folhapagamento.folhapagamento', string='Folha de Pagamento')


class FolhaPagamento(models.Model):
    _name = 'folhapagamento.folhapagamento'
    _description = 'Folha de Pagamento'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Descrição')

    month = fields.Selection(
        [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'),
         ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'),
         ('11', 'November'), ('12', 'December')],
        string='Month',
        required=True,
        help='Month related to the payroll'
    )

    year = fields.Selection(
        [(str(year), str(year)) for year in range(2000, datetime.now().year + 2)],

        string='Ano',
        default=str(datetime.now().year),
        help='Ano relacionado ao pagamento'
    )

    payslip_ids = fields.One2many(
        comodel_name='hr.payslip',
        inverse_name='folhapagamento_id',
        string='Payslips',
        # store=True
    )

    salary_rule_line_ids = fields.One2many(
        comodel_name='hr.payslip.line',
        string='Detalhes de Regra Salarial',
        compute='_compute_salary_rule_line_ids'
    )

    aggregated_salary_rule_lines = fields.One2many(
        comodel_name='folhapagamento.aggregated.line',
        inverse_name='folhapagamento_id',
        string='Linhas Agregadas',
        compute='_compute_aggregated_salary_rule_lines',
        store=False,
        readonly=False,
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

    def action_approve(self):
        for record in self:
            record.state = 'approved'
            record.aprovado_por = self.env.user

    def action_complete(self):
        for record in self:
            record.state = 'completed'
            record.aprovado_por = self.env.user

    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'

    def action_view_report(self):
        print("ID do registro:", self.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'folhareport',
            'params': {
                'id': self.id,
            },
            'context': {
                'params': {
                    'id': self.id,
                }
            },
        }

    def unlink(self):
        # Verifica se existe alguma Folha de Pagamento que não esteja nos estados 'submitted' ou 'cancelled'
        if any(self.filtered(lambda payslip: payslip.state not in ('submitted', 'cancelled'))):
            raise UserError(_("Não é possível excluir uma folha de pagamento que está no estado 'Aprovado' ou 'Concluído'."))

        # Se todas as folhas de pagamento estiverem nos estados permitidos, executa a exclusão
        return super(FolhaPagamento, self).unlink()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        company_id = self.env.company.id
        if company_id:
            args = args or []
            args.append(('company_id', '=', company_id))
        print(f"Empresa ativa no search: {company_id}, Filtros aplicados: {args}")
        return super(FolhaPagamento, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.onchange('month', 'departamento_id', 'year')
    def _onchange_month_or_departamento(self):
        if self.month and self.year:
            # Usando o ano selecionado
            year = int(self.year)
            date_from = datetime.strptime(f'{year}-{self.month}-01', '%Y-%m-%d').date()
            date_to = (date_from.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            domain = [
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
            ]

            if self.departamento_id:
                domain.append(('employee_id.department_id', '=', self.departamento_id.id))


            payslips = self.env['hr.payslip'].search(domain)
            print(f"Payslips encontrados: {payslips.ids}")

            self.payslip_ids = [(6, 0, payslips.ids)]
        else:
            self.payslip_ids = False

    @api.depends('payslip_ids')
    def _compute_salary_rule_line_ids(self):
        for record in self:
            line_ids = record.payslip_ids.mapped('line_ids')
            record.salary_rule_line_ids = line_ids
            print(f"Salary Line IDs Computed: {line_ids}")


    @api.depends('salary_rule_line_ids', 'departamento_id')
    def _compute_aggregated_salary_rule_lines(self):
        AggregatedLine = self.env['folhapagamento.aggregated.line']
        for record in self:

            record.aggregated_salary_rule_lines = [(5, 0, 0)]


            departamento_id = record.departamento_id.id if record.departamento_id else None
            group_by_employee_contract = defaultdict(lambda: {'codes': {}, 'total': 0.0, 'job_position': None})

            for line in record.salary_rule_line_ids:
                if departamento_id and line.employee_id.department_id.id == departamento_id:
                    key = (line.employee_id.id, line.contract_id.id, line.employee_id.barcode,
                           line.employee_id.x_nuit, line.employee_id.x_inss,line.employee_id.birthday)

                    group_by_employee_contract[key]['employee_id'] = line.employee_id.id
                    group_by_employee_contract[key]['x_nuit'] = line.employee_id.x_nuit
                    group_by_employee_contract[key]['x_inss'] = line.employee_id.x_inss
                    group_by_employee_contract[key]['contract_id'] = line.contract_id.id
                    group_by_employee_contract[key]['job_position'] = line.employee_id.job_id.name
                    group_by_employee_contract[key]['codes'][line.code] = line.amount
                    group_by_employee_contract[key]['total'] += line.amount
                    group_by_employee_contract[key]['barcode'] = line.employee_id.barcode
                elif not departamento_id:
                    key = (line.employee_id.id, line.contract_id.id, line.employee_id.barcode)
                    group_by_employee_contract[key]['employee_id'] = line.employee_id.id
                    group_by_employee_contract[key]['x_nuit'] = line.employee_id.x_nuit
                    group_by_employee_contract[key]['birthday'] = line.employee_id.birthday
                    group_by_employee_contract[key]['x_inss'] = line.employee_id.x_inss
                    group_by_employee_contract[key]['contract_id'] = line.contract_id.id
                    group_by_employee_contract[key]['job_position'] = line.employee_id.job_id.name
                    group_by_employee_contract[key]['codes'][line.code] = line.amount
                    group_by_employee_contract[key]['total'] = line.amount
                    group_by_employee_contract[key]['barcode'] = line.employee_id.barcode

            aggregated_lines = []
            for key, values in group_by_employee_contract.items():
                total_remuneracoes = (
                        values['codes'].get('GROSS', 0.0) +
                        values['codes'].get('H_E_200', 0.0) +
                        values['codes'].get('H_E_150', 0.0)
                )

                total_descontos = (
                        values['codes'].get('INSS', 0.0) + values['codes'].get('IRPS', 0.0) +
                        values['codes'].get('D_P_A', 0.0) + values['codes'].get('DIS_F_D', 0.0) +
                        values['codes'].get('DD', 0.0) + values['codes'].get('DPE', 0.0) +
                        values['codes'].get('DFF', 0.0)
                )



                existing_line = AggregatedLine.search([
                    ('folhapagamento_id', '=', record.id),
                    ('employee_id', '=', values['employee_id']),
                    ('contract_id', '=', values['contract_id'])
                ], limit=1)

                if existing_line:

                    existing_line.write({
                        'basic_amount': values['codes'].get('BASIC', 0.0),
                        'inc_amount': values['codes'].get('INC', 0.0),
                        'gross_amount': values['codes'].get('GROSS', 0.0),
                        'inss_amount': values['codes'].get('INSS', 0.0),
                        'net_amount': values['codes'].get('NET', 0.0),
                        'descontoatraso': values['codes'].get('D_P_A', 0.0),
                        'descotofaltasdias': values['codes'].get('DIS_F_D', 0.0),
                        'emprestimos': values['codes'].get('DPE', 0.0),
                        'fundofunebre': values['codes'].get('DFF', 0.0),
                        'horasextrascem': values['codes'].get('H_E_200', 0.0),
                        'horasextrasc': values['codes'].get('H_E_150', 0.0),
                        'irps_amout': values['codes'].get('IRPS', 0.0),
                        'outrosdescontos': values['codes'].get('DD', 0.0),
                        'total_amount': values['total'],
                        'code': values['barcode'],
                        'totalderemuneracoes': total_remuneracoes,
                        'totaldedescontos': total_descontos
                    })


                    aggregated_lines.append(existing_line.id)
                else:


                    aggregated_line = AggregatedLine.create({
                        'folhapagamento_id': record.id,
                        'employee_id': values['employee_id'],
                        'contract_id': values['contract_id'],
                        'job_position': values['job_position'],
                        'basic_amount': values['codes'].get('BASIC', 0.0),
                        'inc_amount': values['codes'].get('INC', 0.0),
                        'gross_amount': values['codes'].get('GROSS', 0.0),
                        'inss_amount': values['codes'].get('INSS', 0.0),
                        'net_amount': values['codes'].get('NET', 0.0),
                        'descontoatraso': values['codes'].get('D_P_A', 0.0),
                        'descotofaltasdias': values['codes'].get('DIS_F_D', 0.0),
                        'emprestimos': values['codes'].get('DPE', 0.0),
                        'fundofunebre': values['codes'].get('DFF', 0.0),
                        'horasextrascem': values['codes'].get('H_E_200', 0.0),
                        'horasextrasc': values['codes'].get('H_E_150', 0.0),
                        'irps_amout': values['codes'].get('IRPS', 0.0),
                        'outrosdescontos': values['codes'].get('DD', 0.0),
                        'total_amount': values['total'],
                        'code': values['barcode'],
                        'totalderemuneracoes': total_remuneracoes,
                        'totaldedescontos': total_descontos
                    })



                    aggregated_lines.append(aggregated_line.id)

            record.aggregated_salary_rule_lines = [(6, 0, aggregated_lines)]

class AggregatedLine(models.Model):
    _name = 'folhapagamento.aggregated.line'
    _description = 'Linha Agregada de Salário'

    folhapagamento_id = fields.Many2one('folhapagamento.folhapagamento', string='Folha de Pagamento',
                                        ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contract')
    job_position = fields.Char(string='Job Position')

    basic_amount = fields.Float(string='BASIC')
    inc_amount = fields.Float(string='INC')
    gross_amount = fields.Float(string='GROSS')
    inss_amount = fields.Float(string='INSS')
    irps_amout = fields.Float(string='IRPS')
    net_amount = fields.Float(string='NET')
    total_amount = fields.Float(string='Total Amount')
    code = fields.Char(string='Código')
    descontoatraso = fields.Float(string="Desconto p/ Atrasos")
    descotofaltasdias = fields.Float(string="Total de Faltas em Dias")
    emprestimos = fields.Float(string="Emprestimos")
    fundofunebre = fields.Float(string="Fundo Fundo")
    horasextrascem = fields.Float(string="Horas Extras 100%")
    horasextrasc = fields.Float(string="Horas Extras 50%")
    outrosdescontos = fields.Float(string="Outros Descontos")

    totalderemuneracoes = fields.Float(string=" total de remuneracoes")
    totaldedescontos = fields.Float(string=" total de descontos")

    def action_example_method(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'folhareport',
        }


