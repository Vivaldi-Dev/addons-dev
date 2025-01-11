from odoo import models

class ReportXls(models.AbstractModel):
    _name = "report.recibodesalario.recibo_report_xls"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, partners):

        worksheet = workbook.add_worksheet('Bank Report')

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

        headers = [
            '#', 'Número da Conta', 'Nome do Funcionário', 'Nome do Banco', 'Função', 'Valor a Depositar'
        ]

        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, header_format)

        sorted_lines = []


        for recipo in partners:
            for line in recipo.linhas_agregadas:
                sorted_lines.append((line, line.employee_id.name or ''))

        row = 1
        for line, employee_name in sorted_lines:

            worksheet.write(row, 0, row, cell_format)
            worksheet.write(row, 1, line.bank_account_number or '', cell_format)
            worksheet.write(row, 2, employee_name, cell_format)
            worksheet.write(row, 3, line.bank_name or '', cell_format)
            worksheet.write(row, 4, line.job_position or '', cell_format)
            worksheet.write(row, 5, line.net_amount or '', cell_format)

            row += 1


        worksheet.set_column(0, len(headers) - 1, 20)

