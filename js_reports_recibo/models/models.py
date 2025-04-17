import base64
import io
import zipfile

from odoo import models, fields, api
from datetime import datetime, timedelta
from collections import defaultdict

from odoo.exceptions import UserError


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    folha_id = fields.Many2one('recibo.recibo', string='Folha de Pagamento')


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    folha_id = fields.Many2one('recibo.recibo', string='Folha de Pagamento')


class Recibo(models.Model):
    _name = 'recibo.recibo'
    _description = 'Folha de Pagamento'

    descricao = fields.Char(string='Descrição')

    mes = fields.Selection(
        [('01', 'Janeiro'), ('02', 'Fevereiro'), ('03', 'Março'), ('04', 'Abril'), ('05', 'Maio'),
         ('06', 'Junho'), ('07', 'Julho'), ('08', 'Agosto'), ('09', 'Setembro'), ('10', 'Outubro'),
         ('11', 'Novembro'), ('12', 'Dezembro')],
        string='Mês',
        required=True,
        help='Mês relacionado à folha de pagamento'
    )

    folhas_payslip_ids = fields.One2many(
        comodel_name='hr.payslip',
        inverse_name='folha_id',
        string='Folhas de Pagamento',
        store=True
    )

    year = fields.Selection(
        [(str(year), str(year)) for year in range(2015, datetime.now().year + 2)],
        string='Ano',
        default=str(datetime.now().year),
        help='Ano relacionado ao pagamento'
    )

    detalhes_regras_salariais_ids = fields.One2many(
        comodel_name='hr.payslip.line',
        string='Detalhes de Regras Salariais',
        compute='_compute_detalhes_regras_salariais_ids'
    )

    linhas_agregadas = fields.One2many(
        comodel_name='folhapagamento.individual.report',
        inverse_name='folha_id',
        string='Linhas Agregadas',
        compute='_compute_linhas_agregadas',
        store=True,
        order='employee_id asc',
        readonly=True,
    )

    Payslip_Worked = fields.One2many(
        comodel_name='hr.payslip.worked_days',
        inverse_name='folha_id',
        string='Payslip Worked Hours'
    )
    estado = fields.Selection(
        [('submitted', 'Submetido'),
         ('approved', 'Aprovado'),
         ('completed', 'Concluído'),
         ('cancelled', 'Cancelado')],
        string='Estado',
        default='submitted',
        required=True
    )

    empresa_id = fields.Many2one(
        'res.company',
        string='Empresa',
        readonly=True,
        copy=False,
        help="Empresa",
        default=lambda self: self.env['res.company']._company_default_get()
    )

    departamento_id = fields.Many2one('hr.department', string='Departamento de RH')
    employee_id = fields.Many2one('hr.employee', string='Employee', )

    def acao_visualizar_relatorio(self):
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

    def action_download_txt_from_aggregated_lines(self):
        self.ensure_one()
        aggregated_lines = self.linhas_agregadas
        if not aggregated_lines:
            raise UserError("Nenhuma linha agregada encontrada.")

        return aggregated_lines[0].action_download_txt()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        empresa_id = self.env.company.id
        if empresa_id:
            args = args or []
            args.append(('empresa_id', '=', empresa_id))
        print(f"Empresa ativa no search: {empresa_id}, Filtros aplicados: {args}")
        return super(Recibo, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.onchange('mes', 'departamento_id', 'year')
    def _onchange_month_or_departamento(self):
        if self.mes and self.year:

            year = int(self.year)
            date_from = datetime.strptime(f'{year}-{self.mes}-01', '%Y-%m-%d').date()
            date_to = (date_from.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            domain = [
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
            ]

            if self.departamento_id:
                domain.append(('employee_id.department_id', '=', self.departamento_id.id))

            payslips = self.env['hr.payslip'].search(domain)
            print(f"Payslips encontrados: {payslips.ids}")

            self.folhas_payslip_ids = [(6, 0, payslips.ids)]
        else:
            self.folhas_payslip_ids = False

    @api.depends('folhas_payslip_ids')
    def _compute_detalhes_regras_salariais_ids(self):
        for registro in self:
            line_ids = registro.folhas_payslip_ids.mapped('line_ids')
            registro.detalhes_regras_salariais_ids = line_ids
            print(f"Salary Line IDs Computed: {line_ids}")

    def _filtrar_e_agrupar_linhas(self, departamento_id=None, employee_id=None):
        """Filtra e agrupa as linhas de regras salariais."""
        agrupado_por_contrato = defaultdict(lambda: {'codes': {}, 'total': 0.0, 'job_position': None})

        for linha in self.detalhes_regras_salariais_ids:

            if departamento_id and linha.employee_id.department_id.id != departamento_id:
                continue
            if employee_id and linha.employee_id.id != employee_id:
                continue

            chave = (linha.employee_id.id, linha.contract_id.id, linha.employee_id.barcode, linha.employee_id.x_nuit,
                     linha.employee_id.x_inss,linha.employee_id.birthday)
            grupo = agrupado_por_contrato[chave]

            grupo['employee_id'] = linha.employee_id.id
            grupo['x_nuit'] = linha.employee_id.x_nuit
            grupo['birthday'] = linha.employee_id.birthday
            grupo['x_inss'] = linha.employee_id.x_inss
            grupo['contract_id'] = linha.contract_id.id
            grupo['job_position'] = linha.employee_id.job_id.name
            grupo['codes'][linha.code] = linha.amount
            grupo['total'] += linha.amount
            grupo['barcode'] = linha.employee_id.barcode

        return agrupado_por_contrato

    def _calcular_totais(self, codes):
        """Calcula os totais de remunerações e descontos."""
        total_remuneracoes = (
                codes.get('GROSS', 0.0) +
                codes.get('H_E_200', 0.0) +
                codes.get('H_E_150', 0.0)
        )
        total_descontos = (
                codes.get('INSS', 0.0) + codes.get('IRPS', 0.0) +
                codes.get('D_P_A', 0.0) + codes.get('DIS_F_D', 0.0) +
                codes.get('DD', 0.0) + codes.get('DPE', 0.0) +
                codes.get('DFF', 0.0)
        )
        return total_remuneracoes, total_descontos

    def _atualizar_ou_criar_linhas(self, AggregatedLine, registro, agrupado_por_contrato):
        """Atualiza ou cria as linhas agregadas."""
        linhas_agregadas = []
        for chave, valores in agrupado_por_contrato.items():
            total_remuneracoes, total_descontos = self._calcular_totais(valores['codes'])

            employee = self.env['hr.employee'].browse(valores['employee_id'])

            date_from = datetime.strptime(f"{registro.year}-{registro.mes}-01", '%Y-%m-%d').date()
            date_to = (date_from.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            payslip_worked_days = self.env['hr.payslip.worked_days'].search([
                ('payslip_id.employee_id', '=', valores['employee_id']),
                ('payslip_id.date_from', '>=', date_from),
                ('payslip_id.date_to', '<=', date_to)
            ])
            total_worked_days = sum(payslip_worked_days.mapped('number_of_days'))

            leaves = self.env['hr.leave'].sudo().search([
                ('employee_id', '=', valores['employee_id']),
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to),
                ('state', 'in', ['confirm', 'refuse'])
            ])

            name_absent = ''
            leave_type = ''
            total_leaves = 0
            unique_codes = set()
            data_check_in = False

            for leave in leaves:
                total_leaves += (leave.date_to - leave.date_from).days + 1
                if leave.holiday_status_id:
                    unique_codes.add(leave.holiday_status_id.code)
                    name_absent = leave.holiday_status_id.name
                    leave_type = leave.holiday_status_id.leave_type

                if not data_check_in or leave.date_from < data_check_in:
                    data_check_in = leave.date_from

            code_absent = unique_codes.pop() if unique_codes else ''


            bank_account_number = False
            bank_name = False
            if employee.address_home_id.bank_ids:
                bank_account_number = employee.address_home_id.bank_ids[0].acc_number
                bank_name = employee.address_home_id.bank_ids[0].bank_id.name

            gross_amount = int(valores['codes'].get('GROSS', 0.0))

            data = {
                'folha_id': registro.id,
                'employee_id': valores['employee_id'],
                'contract_id': valores['contract_id'],
                'job_position': valores['job_position'],
                'basic_amount': valores['codes'].get('BASIC', 0.0),
                'inc_amount': valores['codes'].get('INC', 0.0),
                'gross_amount': gross_amount,
                'inss_amount': valores['codes'].get('INSS', 0.0),
                'net_amount': valores['codes'].get('NET', 0.0),
                'descontoatraso': valores['codes'].get('D_P_A', 0.0),
                'descotofaltasdias': valores['codes'].get('DIS_F_D', 0.0),
                'emprestimos': valores['codes'].get('DPE', 0.0),
                'fundofunebre': valores['codes'].get('DFF', 0.0),
                'horasextrascem': valores['codes'].get('H_E_200', 0.0),
                'horasextrasc': valores['codes'].get('H_E_150', 0.0),
                'irps_amout': valores['codes'].get('IRPS', 0.0),
                'outrosdescontos': valores['codes'].get('DD', 0.0),
                'total_amount': valores['total'],
                'code': valores['barcode'],
                'birthday': valores['birthday'],
                'numero_contribuinte': valores['x_nuit'],
                'numero_beneficiario': valores['x_inss'],
                'totalderemuneracoes': total_remuneracoes,
                'totaldedescontos': total_descontos,
                'bank_account_number': bank_account_number,
                'bank_name': bank_name,
                'worked_days': total_worked_days,
                'total_leaves': total_leaves,
                'code_absent': code_absent,
                'name_absent': name_absent,
                'leave_type': leave_type,
                'data_check_in': data_check_in,
                'company_registry': registro.empresa_id.company_registry,
            }

            linha_existente = AggregatedLine.search([
                ('folha_id', '=', registro.id),
                ('employee_id', '=', valores['employee_id']),
                ('contract_id', '=', valores['contract_id'])
            ], limit=1)

            if linha_existente:
                linha_existente.write(data)
                linhas_agregadas.append(linha_existente.id)
            else:
                nova_linha = AggregatedLine.create(data)
                linhas_agregadas.append(nova_linha.id)

        return linhas_agregadas

    @api.depends('detalhes_regras_salariais_ids', 'employee_id')
    def _compute_linhas_agregadas(self):
        AggregatedLine = self.env['folhapagamento.individual.report']
        for registro in self:
            agrupado_por_contrato = self._filtrar_e_agrupar_linhas(
                departamento_id=None,
                employee_id=registro.employee_id.id
            )

            linhas_agregadas = self._atualizar_ou_criar_linhas(AggregatedLine, registro, agrupado_por_contrato)

            registro.linhas_agregadas = [(6, 0, linhas_agregadas)]


class AggregatedLine(models.Model):
    _name = 'folhapagamento.individual.report'
    _description = 'Linha Agregada de Salário'

    folha_id = fields.Many2one('recibo.recibo', string='Folha de Pagamento',
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

    bank_account_number = fields.Char(string='Número da Conta Bancária')
    bank_name = fields.Char(string='Nome do Banco')

    code_absent = fields.Char(string="Codigo da falta")

    name_absent = fields.Char(string="Nome da falta")

    leave_type = fields.Char(string="Tipo de falta")
    data_check_in = fields.Date(string="")

    worked_days = fields.Float(string='Dias Trabalhados')
    total_leaves = fields.Float(string='Total de Faltas')

    birthday = fields.Date(string="Data de Aniversário")

    company_registry = fields.Char(string='Registro da Empresa', related='folha_id.empresa_id.company_registry',
                                   store=True)
    def action_example_method(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'folhareport',
        }

    def _get_lines_txt(self, docs):
        lines = []
        for doc in docs:
            for linha in doc.linhas_agregadas:
                line = '%s;%s;%s;%s;%s;%s;%s' % (
                    (linha.numero_beneficiario or '').strip(),
                    str(int(
                        linha.worked_days - linha.total_leaves)) if linha.worked_days and linha.total_leaves else '',
                    str(int(linha.basic_amount)) if linha.basic_amount else '',
                    '{:.1f}'.format(linha.inc_amount).strip() if linha.inc_amount else '',
                    (linha.code_absent or '').strip(),
                    linha.data_check_in.strftime('%d%m%Y') if linha.data_check_in else '',
                    (linha.leave_type or '').strip()
                )
                lines.append(line)
        return '\n'.join(lines)

    def render_txt(self, docids, data=None):
        docs = self.env['folhapagamento.individual.report'].browse(docids)
        txt_data = self._get_lines_txt(docs)
        return txt_data

    def action_download_txt(self):
        txt_content = self.env['report.js_reports_recibo.recibo_report_inss'].render_txt(self.ids)
        output = io.BytesIO()
        output.write(txt_content.encode('utf-8'))
        output.seek(0)

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=%s&id=%s&field=raw_file&filename=INSS.txt&download=true' % (
                self._name, self.id),
            'target': 'self',
        }

class ReportINSS(models.AbstractModel):
    _name = 'report.js_reports_recibo.recibo_report_inss'
    _description = 'Relatório INSS em TXT'

    @api.model
    def render_txt(self, docids, data=None):
        records = self.env['folhapagamento.individual.report'].browse(docids)
        lines = []
        for linha in records:
            line = '%s;%s;%s;%s;%s;%s;%s' % (
                (linha.numero_beneficiario or '').strip(),
                str(int(linha.worked_days - linha.total_leaves)) if linha.worked_days and linha.total_leaves else '',
                str(int(linha.basic_amount)) if linha.basic_amount else '',
                '{:.1f}'.format(linha.inc_amount).strip() if linha.inc_amount else '',
                (linha.code_absent or '').strip(),
                linha.data_check_in.strftime('%d%m%Y') if linha.data_check_in else '',
                (linha.leave_type or '').strip()
            )
            lines.append(line)
        return '\n'.join(lines)
