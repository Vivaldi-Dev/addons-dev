from odoo import models, fields, api, exceptions,_
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from collections import defaultdict


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    folhapagamento_id = fields.Many2one('folhapagamento.folhapagamento', string='Folha de Pagamento')


class FolhaPagamento(models.Model):
    _name = 'folhapagamento.folhapagamento'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Folha de Pagamento'

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
        inverse_name='folhapagamento_id',
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
        inverse_name='folhapagamento_id',
        string='Linhas Agregadas',
        compute='_compute_aggregated_salary_rule_lines',
        store=True,
        order='employee_id asc'
    )

    aggregated_salary_rule_lines_irps = fields.One2many(
        comodel_name='folhapagamento.aggregated.line',
        inverse_name='folhapagamento_id',
        string='Linhas Agregadas',
        compute='_compute_aggregated_salary_rule_lines',
        store=True,
        domain=[('irps_amout', '!=', 0)]
    )

    aggregated_salary_rule_lines_inss = fields.One2many(
        comodel_name='folhapagamento.aggregated.line',
        inverse_name='folhapagamento_id',
        string='Linhas Agregadas',
        compute='_compute_aggregated_salary_rule_lines',
        store=True,
        domain=[('inss_amount', '!=', 0)]
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

    @api.model
    def unlink(self):
        if any(record.state == 'approved' for record in self):
            raise ValidationError(_(
                "Não é possível excluir uma folha de pagamento que está no estado 'Aprovado'."))

        return super(FolhaPagamento, self).unlink()

    # @api.multi
    # def unlink(self):
    #     for order in self:
    #         if order.state not in ('draft', 'cancel'):
    #          raise UserError(_('You can not delete a sent quotation or a sales order! Try to cancel it before.'))
    #
    #     return super(FolhaPagamento, self).unlink()



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

    @api.onchange('departamento_id')
    def _onchange_departamento_id(self):
        if self.departamento_id:
            self._apply_department_filter()

    def _apply_department_filter(self):
        if self.month:
            year = datetime.now().year
            date_from = datetime.strptime(f'{year}-{self.month}-01', '%Y-%m-%d').date()
            date_to = (date_from.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            payslips = self.env['hr.payslip'].search([

                ('employee_id.department_id', '=', self.departamento_id.id),
            ])

            self.payslip_ids = [(6, 0, payslips.ids)]

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

            departamento_id = record.departamento_id.id if record.departamento_id else None
            group_by_employee_contract = defaultdict(lambda: {'codes': {}, 'total': 0.0, 'job_position': None})

            for line in record.salary_rule_line_ids:
                if departamento_id and line.employee_id.department_id.id == departamento_id:
                    key = (line.employee_id.id, line.contract_id.id, line.employee_id.barcode,
                           line.employee_id.x_nuit, line.employee_id.x_inss)

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

                irps_amount = values['codes'].get('IRPS', 0.0)
                if irps_amount < 0:
                    irps_amount = -irps_amount

                inss_amount = values['codes'].get('INSS', 0.0)
                if inss_amount < 0:
                    inss_amount = -inss_amount

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
                        'inss_amount_positivo': inss_amount,
                        'net_amount': values['codes'].get('NET', 0.0),
                        'descontoatraso': values['codes'].get('D_P_A', 0.0),
                        'descotofaltasdias': values['codes'].get('DIS_F_D', 0.0),
                        'emprestimos': values['codes'].get('DPE', 0.0),
                        'fundofunebre': values['codes'].get('DFF', 0.0),
                        'horasextrascem': values['codes'].get('H_E_200', 0.0),
                        'horasextrasc': values['codes'].get('H_E_150', 0.0),
                        'irps_amout': values['codes'].get('IRPS', 0.0),
                        'irps_amout_positivo': irps_amount,
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
                        'inss_amount_positivo': inss_amount,
                        'net_amount': values['codes'].get('NET', 0.0),
                        'descontoatraso': values['codes'].get('D_P_A', 0.0),
                        'descotofaltasdias': values['codes'].get('DIS_F_D', 0.0),
                        'emprestimos': values['codes'].get('DPE', 0.0),
                        'fundofunebre': values['codes'].get('DFF', 0.0),
                        'horasextrascem': values['codes'].get('H_E_200', 0.0),
                        'horasextrasc': values['codes'].get('H_E_150', 0.0),
                        'irps_amout': values['codes'].get('IRPS', 0.0),
                        'irps_amout_positivo': irps_amount,
                        'outrosdescontos': values['codes'].get('DD', 0.0),
                        'total_amount': values['total'],
                        'code': values['barcode'],
                        'numero_contribuinte': values['x_nuit'],
                        'numero_beneficiario': values['x_inss'],
                        'totalderemuneracoes': total_remuneracoes,
                        'totaldedescontos': total_descontos
                    })
                    record.aggregated_salary_rule_lines = [(4, line_id) for line_id in aggregated_lines]
                    record.aggregated_salary_rule_lines_irps = [(4, line_id) for line_id in aggregated_lines]
                    record.aggregated_salary_rule_lines_inss = [(4, line_id) for line_id in aggregated_lines]


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
    irps_amout_positivo = fields.Float(string='IRPS')
    inss_amount_positivo = fields.Float(string='INSS')

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

    numero_contribuinte = fields.Char(string='Nº de Contribuinte')
    numero_beneficiario = fields.Char(string='Nº de Beneficiário')

    def action_example_method(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'folhareport',
        }
