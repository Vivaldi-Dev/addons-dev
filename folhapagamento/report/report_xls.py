from odoo import models


class ReportXls(models.AbstractModel):
    _name = "report.folhapagamento.folhapagamento_report_xls"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):
        # Criação da aba "Folha de Pagamento"
        worksheet = workbook.add_worksheet('Folha de Pagamento')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'align': 'center',
            'border': 1,
            'font_size': 10,
        })
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'font_size': 10,
        })

        # Cabeçalhos conforme fornecido
        headers = [
            '#', 'Nome do Funcionário', 'Função', 'Venc Base', 'Incentivo',
            'H.E', 'Total Rem', 'INSS', 'IRPS', 'Atrasos',
            'Faltas Dias', 'Emprest', 'Fundo Funebre', 'Diversos',
            'Total Desc', 'A Receber'
        ]

        # Escrever os cabeçalhos na primeira linha
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        # Ordenar a lista de 'partners' com base no nome do funcionário
        sorted_lines = []

        for folhapagamento in partners:
            for line in folhapagamento.aggregated_salary_rule_lines:
                # Adiciona as linhas à lista 'sorted_lines', junto com o nome do funcionário
                sorted_lines.append((line, line.employee_id.name or ''))

        # Ordenar pelo nome do funcionário
        sorted_lines.sort(
            key=lambda x: x[1].lower())  # Ordena por nome em ordem alfabética (ignorando maiúsculas/minúsculas)

        # Inicializar variáveis para acumular os totais
        total_venc_base = 0
        total_incentivo = 0
        total_he = 0
        total_rem = 0
        total_inss = 0
        total_irps = 0
        total_atrasos = 0
        total_faltas_dias = 0
        total_emprest = 0
        total_fundo_funebre = 0
        total_diversos = 0
        total_desc = 0
        total_a_receber = 0

        # Preencher a planilha com as linhas ordenadas
        row = 1
        for line, employee_name in sorted_lines:
            worksheet.write(row, 0, row, cell_format)  # Número
            worksheet.write(row, 1, employee_name, cell_format)  # Nome do Funcionário
            worksheet.write(row, 2, line.job_position or '', cell_format)
            worksheet.write(row, 3, line.basic_amount, cell_format)
            worksheet.write(row, 4, line.inc_amount, cell_format)
            worksheet.write(row, 5, line.horasextrasc + line.horasextrascem, cell_format)
            worksheet.write(row, 6, line.gross_amount, cell_format)
            worksheet.write(row, 7, line.inss_amount, cell_format)
            worksheet.write(row, 8, line.irps_amout, cell_format)
            worksheet.write(row, 9, line.descontoatraso, cell_format)
            worksheet.write(row, 10, line.descotofaltasdias, cell_format)
            worksheet.write(row, 11, line.emprestimos, cell_format)
            worksheet.write(row, 12, line.fundofunebre, cell_format)
            worksheet.write(row, 13, line.outrosdescontos, cell_format)
            worksheet.write(row, 14, line.totaldedescontos, cell_format)
            worksheet.write(row, 15, line.net_amount, cell_format)

            # Acumulando os totais
            total_venc_base += line.basic_amount
            total_incentivo += line.inc_amount
            total_he += (line.horasextrasc + line.horasextrascem)
            total_rem += line.gross_amount
            total_inss += line.inss_amount
            total_irps += line.irps_amout
            total_atrasos += line.descontoatraso
            total_faltas_dias += line.descotofaltasdias
            total_emprest += line.emprestimos
            total_fundo_funebre += line.fundofunebre
            total_diversos += line.outrosdescontos
            total_desc += line.totaldedescontos
            total_a_receber += line.net_amount

            row += 1

        # Escrever os totais na última linha
        worksheet.write(row, 0, 'Total', header_format)  # Rótulo de Totais
        worksheet.write(row, 3, total_venc_base, cell_format)
        worksheet.write(row, 4, total_incentivo, cell_format)
        worksheet.write(row, 5, total_he, cell_format)
        worksheet.write(row, 6, total_rem, cell_format)
        worksheet.write(row, 7, total_inss, cell_format)
        worksheet.write(row, 8, total_irps, cell_format)
        worksheet.write(row, 9, total_atrasos, cell_format)
        worksheet.write(row, 10, total_faltas_dias, cell_format)
        worksheet.write(row, 11, total_emprest, cell_format)
        worksheet.write(row, 12, total_fundo_funebre, cell_format)
        worksheet.write(row, 13, total_diversos, cell_format)
        worksheet.write(row, 14, total_desc, cell_format)
        worksheet.write(row, 15, total_a_receber, cell_format)

        # Ajustar o tamanho das colunas
        worksheet.set_column(0, len(headers) - 1, 15)
