import base64
import io
import zipfile

from odoo import models, fields, api
from datetime import datetime, timedelta
from collections import defaultdict


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



    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        empresa_id = self.env.company.id
        if empresa_id:
            args = args or []
            args.append(('empresa_id', '=', empresa_id))
        print(f"Empresa ativa no search: {empresa_id}, Filtros aplicados: {args}")
        return super(Recibo, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.onchange('mes')
    def _onchange_mes(self):
        if self.mes:
            ano = datetime.now().year
            data_inicio = datetime.strptime(f'{ano}-{self.mes}-01', '%Y-%m-%d').date()
            data_fim = (data_inicio.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            folhas = self.env['hr.payslip'].search([
                ('date_from', '>=', data_inicio),
                ('date_to', '<=', data_fim),
            ])

            self.folhas_payslip_ids = [(6, 0, folhas.ids)]

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
                     linha.employee_id.x_inss)
            grupo = agrupado_por_contrato[chave]

            grupo['employee_id'] = linha.employee_id.id
            grupo['x_nuit'] = linha.employee_id.x_nuit
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

            data = {
                'folha_id': registro.id,
                'employee_id': valores['employee_id'],
                'contract_id': valores['contract_id'],
                'job_position': valores['job_position'],
                'basic_amount': valores['codes'].get('BASIC', 0.0),
                'inc_amount': valores['codes'].get('INC', 0.0),
                'gross_amount': valores['codes'].get('GROSS', 0.0),
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
                'numero_contribuinte': valores['x_nuit'],
                'numero_beneficiario': valores['x_inss'],
                'totalderemuneracoes': total_remuneracoes,
                'totaldedescontos': total_descontos
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
            # Filtrar e agrupar linhas
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

    def action_example_method(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'folhareport',
        }

    @api.model
    def generate_individual_report(self):
        report_name = 'recibodesalario.recibo_report_individual_template'

        report = self.env.ref(report_name)
        pdf_content, _ = report.render_qweb_pdf([self.id])

        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

        return {
            'type': 'ir.actions.act_url',
            'url': 'data:application/pdf;base64,' + pdf_base64,
            'target': 'new',
            'name': 'Relatório Individual',
        }
