# -*- coding: utf-8 -*-
import io
import json
import os
import werkzeug
import xlsxwriter
from odoo import http
from odoo.http import request
import calendar
from datetime import datetime


class Mapa(http.Controller):
    @http.route('/mapa/mapa/<int:id>', auth='none', methods=['GET'], )
    def index(self, id,**kw):

        try:
            record = request.env['mapa.mapa'].sudo().search([('id', '=', id)])
            if not record:
                return werkzeug.wrappers.Response(json.dumps({'error': 'no record Found'}),  headers={'Content-Type': 'application/json'},status=404)

            aggregated_lines = []
            for line in record.aggregated_salary_rule_lines:
                aggregated_line_data = {
                    'codigo_funcionario': line.codigo_funcionario,
                    'employee_id': line.employee_id.name,
                    'numero_contribuinte': line.numero_contribuinte,
                    'numero_beneficiario': line.numero_beneficiario,
                    'irps_amout': line.irps_amout,

                }
                aggregated_lines.append(aggregated_line_data)

            data = {
                'id': record.id,
                'name': record.name,
                'month': record.month,
                'company': record.company_id.name,
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

    @http.route('/mapa/excel/', auth='none', methods=['POST'], csrf=False)
    def export_excel(self, **kw):
        try:
            record = request.env['mapa.mapa'].sudo().search([])
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Mapa IRPS')

            header_format = workbook.add_format({
                'bold': True, 'align': 'center', 'valign': 'vcenter',
                'bg_color': '#D9EAD3', 'border': 1
            })
            data_format = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            number_format = workbook.add_format({
                'num_format': '#,##0.00', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            total_format = workbook.add_format({
                'bold': True, 'bg_color': '#F4CCCC', 'align': 'center',
                'valign': 'vcenter', 'border': 1
            })

            worksheet.merge_range('C1:G1',  f'Mapa de IRPS' , header_format)
            worksheet.merge_range('C2:G2', f'Nome da Empresa:{record.company_id.name} ', data_format)
            worksheet.merge_range('C4:G4', f'Período: {record.name}', data_format)


            headers = ['Código do Funcionário', 'Nome', 'Nº de Contribuinte', 'Nº de Beneficiário', 'Valor']
            for col_num, header in enumerate(headers, start=2):
                worksheet.write(5, col_num, header, header_format)

            total_value = 0
            row_start = 6
            for row_num, line in enumerate(record.aggregated_salary_rule_lines, start=row_start):
                worksheet.write(row_num, 2, line.codigo_funcionario, data_format)
                worksheet.write(row_num, 3, line.employee_id.name, data_format)
                worksheet.write(row_num, 4, line.numero_contribuinte, data_format)
                worksheet.write(row_num, 5, line.numero_beneficiario, data_format)
                worksheet.write(row_num, 6, line.irps_amout, number_format)
                total_value += line.irps_amout

            total_row = row_start + len(record.aggregated_salary_rule_lines)
            worksheet.write(total_row, 2, 'Total', total_format)
            worksheet.write(total_row, 6, total_value, number_format)

            worksheet.set_column(2, 2, 20)
            worksheet.set_column(3, 3, 25)
            worksheet.set_column(4, 4, 20)
            worksheet.set_column(5, 5, 20)
            worksheet.set_column(6, 6, 15)

            workbook.close()
            output.seek(0)

            return http.send_file(
                output,
                filename=f'mapa_irps_{record.name}.xlsx',
                as_attachment=True,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

        except Exception as e:
            return http.Response(
                json.dumps({"error": str(e)}),
                headers={'Content-Type': 'application/json'},
                status=500
            )

