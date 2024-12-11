import io
import json
import os
import werkzeug
import xlsxwriter
from odoo import http
from odoo.http import request
import calendar
from datetime import datetime


class FolhapagamentoController(http.Controller):
    @http.route('/folhapagamento/data/<int:id>', auth='public')
    def index(self, id, **kw):
        try:
            record = request.env['folhapagamento.folhapagamento'].sudo().search([('id', '=', id)], limit=1)
            if not record:
                return werkzeug.wrappers.Response(
                    json.dumps({"error": "Record not found"}),
                    headers={'Content-Type': 'application/json'},
                    status=404
                )

            aggregated_lines = []
            for line in record.aggregated_salary_rule_lines:
                aggregated_line_data = {
                    'employee_id': line.employee_id.id,
                    'employee_name': line.employee_id.name,
                    'contract_id': line.contract_id.id,
                    'department_id': line.employee_id.department_id.name,
                    'contract_name': line.contract_id.name,
                    'job_position': line.job_position,
                    'basic_amount': line.basic_amount,
                    'inc_amount': line.inc_amount,
                    'irps_amout': line.irps_amout,
                    'gross_amount': line.gross_amount,
                    'inss_amount': line.inss_amount,
                    'net_amount': line.net_amount,
                    'outrosdescontos': line.outrosdescontos,
                    'total_amount': line.total_amount,
                    'code': line.code,
                    'descontoatraso': line.descontoatraso,
                    'descotofaltasdias': line.descotofaltasdias,
                    'emprestimos': line.emprestimos,
                    'fundofunebre': line.fundofunebre,
                    'horasextrascem': line.horasextrascem,
                    'horasextrasc': line.horasextrasc,
                    'totalderemuneracoes': line.totalderemuneracoes,
                    'totaldedescontos': line.totaldedescontos,
                }
                aggregated_lines.append(aggregated_line_data)

            data = {
                'id': record.id,
                'name': record.name,
                'month': record.month,
                'company': record.company_id.name,
                'departamento_id': record.departamento_id.name,
                'aprovado_por': record.aprovado_por.name,
                'aggregated_salary_rule_lines': aggregated_lines,
            }

            return werkzeug.wrappers.Response(
                json.dumps(data),
                headers={'Content-Type': 'application/json'},
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({"error": str(e)}),
                headers={'Content-Type': 'application/json'},
                status=500
            )

    @http.route('/folhapagamento/excel', type='http', auth='none', methods=['POST'], csrf=False)
    def download_excel(self):
        try:
            user_home = os.path.expanduser('~')
            downloads_path = os.path.join(user_home, 'Downloads')
            output_path = os.path.join(downloads_path, 'folha_salario_estrutura.xlsx')

            workbook = xlsxwriter.Workbook(output_path)
            sheet = workbook.add_worksheet('Folha de Salário')

            title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
            subtitle_format = workbook.add_format({'italic': True, 'font_size': 12, 'align': 'center'})
            header_format = workbook.add_format(
                {'bold': True, 'font_color': 'white', 'bg_color': '#4F81BD', 'align': 'center', 'border': 1})
            section_header_format = workbook.add_format(
                {'bold': True, 'bg_color': '#D9E1F2', 'align': 'center', 'border': 1})
            text_format = workbook.add_format({'border': 1, 'align': 'center'})
            currency_format = workbook.add_format({'num_format': 'MT #,##0.00', 'border': 1})


            sheet.set_zoom(85)

            folha = request.env['folhapagamento.folhapagamento'].sudo().search([], limit=1, order='id desc')
            if not folha:
                raise ValueError("Nenhum dado encontrado na tabela de folha de pagamento.")

            company_name = folha.company_id.name or "Nome da Empresa"

            sheet.merge_range('A1:P1', company_name, title_format)
            sheet.merge_range('A2:P2', 'Departamento: Recursos Humanos', subtitle_format)
            sheet.merge_range('D4:P4', 'Folha de Salário', header_format)

            meses = {
                '01': "Janeiro", '02': "Fevereiro", '03': "Março", '04': "Abril", '05': "Maio", '06': "Junho",
                '07': "Julho", '08': "Agosto", '09': "Setembro", '10': "Outubro", '11': "Novembro", '12': "Dezembro"
            }

            mes_formatado = f"{meses.get(folha.month, 'Mês Desconhecido')} de {datetime.now().year}"

            sheet.merge_range('D5:P5', f'Referente ao {mes_formatado}', subtitle_format)

            sheet.merge_range('D8:F8', 'Remuneração', section_header_format)
            sheet.merge_range('G8:J8', 'Descontos', section_header_format)

            headers = [
                "Cod", "Nome", "Função",
                "Salário Base", "Incentivo", "Horas Extras",
                "Desconto p/ Atrasos", "Faltas em Dias", "Empréstimos", "Fundo Funebre", "Diversos",
                "INSS", "IRPS", "Valor a Receber"
            ]
            for col, header in enumerate(headers):
                sheet.write(9, col, header, header_format)
                sheet.set_column(col, col, 13)

            dados = []
            for aggregated_line in folha.aggregated_salary_rule_lines:
                horas_extras = aggregated_line.horasextrasc + aggregated_line.horasextrascem
                dados.append([
                    aggregated_line.code,
                    aggregated_line.employee_id.name if aggregated_line.employee_id else '',
                    aggregated_line.job_position,
                    aggregated_line.basic_amount,
                    aggregated_line.inc_amount,
                    horas_extras,
                    aggregated_line.descontoatraso,
                    aggregated_line.descotofaltasdias,
                    aggregated_line.emprestimos,
                    aggregated_line.fundofunebre,
                    aggregated_line.outrosdescontos,
                    aggregated_line.inss_amount,
                    aggregated_line.irps_amout,
                    aggregated_line.net_amount,
                ])

            row = 10

            for linha in dados:
                for col, valor in enumerate(linha):
                    if isinstance(valor, (int, float)):
                        sheet.write(row, col, valor, currency_format)
                    else:
                        sheet.write(row, col, valor, text_format)
                row += 1

            sheet.write(row, 0, 'Total Geral', header_format)
            for col in range(3, len(headers)):
                col_letter = xlsxwriter.utility.xl_col_to_name(col)
                sheet.write_formula(row, col, f'=SUM({col_letter}10:{col_letter}{row})', currency_format)

            departamento_rh = folha.departamento_id.name or "Departamento não informado"
            aprovado_por = folha.aprovado_por.name or "Aprovador não informado"

            sheet.merge_range(f'A{row + 3}:C{row + 3}', 'Departamento de RH:', subtitle_format)
            sheet.merge_range(f'A{row + 4}:C{row + 4}', f'{departamento_rh}', text_format)
            sheet.merge_range(f'G{row + 3}:H{row + 3}', 'Aprovado Por:', subtitle_format)
            sheet.merge_range(f'G{row + 4}:H{row + 4}', f'{aprovado_por}', text_format)

            workbook.close()

            with open(output_path, 'rb') as f:
                file_content = f.read()

            return request.make_response(
                file_content,
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                    ('Content-Disposition', f'attachment; filename="folha_salario_estrutura.xlsx"')
                ]
            )

        except Exception as e:
            error_message = {"error": str(e)}
            return werkzeug.wrappers.Response(
                json.dumps(error_message),
                headers={'Content-Type': 'application/json'},
                status=500
            )






