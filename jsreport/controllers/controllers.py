# -*- coding: utf-8 -*-
import base64
import json
import werkzeug.wrappers
from odoo import http
from odoo.http import request, _logger
from datetime import datetime
import logging


class fetchData(http.Controller):

    @http.route('/report/fetchData', auth='none', methods=['GET'], csrf=False)
    def fetchData(self, **kw):
        try:
            report = request.env['subconta.subconta'].sudo().search([])
            data = []

            for row in report:
                data.append({
                    'id': row.id,
                    'name': row.name,
                })

            return werkzeug.wrappers.Response(
                json.dumps(data),
                headers={'Content-Type': 'application/json'},
                status=200
            )

        except Exception as e:
            error_message = {
                'error': 'Ocorreu um erro ao buscar os dados',
                'details': str(e)
            }
            return werkzeug.wrappers.Response(json.dumps(error_message), headers={'Content-Type': 'application/json'},
                                              status=500)

    @http.route('/report/fetchData/<int:id>', auth='none', methods=['GET'], csrf=False)
    def fetchData2(self, id, **kw):
        try:

            report = request.env['subconta.subconta'].sudo().search([('id', '=', id)], limit=1)

            if not report:
                return werkzeug.wrappers.Response(
                    json.dumps({'error': 'Subconta com o ID fornecido não foi encontrada'}),
                    headers={'Content-Type': 'application/json'},
                    status=404
                )
            create_date = report.create_date.strftime('%Y-%m-%dT%H:%M:%S') if report.create_date else None

            subconta = {
                'id': report.id,
                'name': report.name,
                'balance': report.balance,
                'order_number': report.order_number,
                'create_date': create_date,
                'item_ids': [
                    {
                        'id': item.id,
                        'item_name': item.name,
                        'amount': item.amount
                    } for item in report.item_ids
                ]
            }

            return werkzeug.wrappers.Response(
                json.dumps(subconta),
                headers={'Content-Type': 'application/json'},
                status=200
            )

        except Exception as e:

            error_message = {
                'error': 'Ocorreu um erro ao buscar os dados',
                'details': str(e)
            }
            return werkzeug.wrappers.Response(
                json.dumps(error_message),
                headers={'Content-Type': 'application/json'},
                status=500
            )

    @http.route('/report/download/<int:report_id>', type='http', auth="public", methods=['GET'], website=True)
    def download_report(self, report_id, **kwargs):
        report = request.env['subconta.subconta'].sudo().search([('id', '=', report_id)], limit=1)

        if not report:
            _logger.warning(f'Relatório com ID {report_id} não encontrado.')
            return request.not_found()

        pdf_content = request.env['ir.actions.report'].sudo()._render_qweb_pdf(report.id)

        filename = f"relatorio_{report_id}.pdf"
        return request.make_response(pdf_content[0], [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename={filename};')
        ])

    @http.route('/postdata', auth="none", methods=['POST'], type='json', csrf=False)
    def postdatas(self, **kw):
        data = request.httprequest.json

        id = data.get('id')
        nome = data.get('nome')

        datas = {
            'id': id,
            'nome': nome,
            'message': 'Dados recebidos com sucesso'
        }

        return datas

    @http.route('/report/subcontas/<int:id>', auth="none", methods=['GET'])
    def report_report(self, id, **kw):

        relatorio = request.env['relatorio.relatorio'].sudo().search([
            ('id', '=', id),
        ], limit=1)

        if not relatorio:
            return werkzeug.wrappers.Response(
                json.dumps({'error': 'Relatório não encontrado ou você não tem permissão para acessá-lo'}),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        relatorio.flush()

        data = {
            'id': relatorio.id,
            'name': relatorio.name,
            'company_id': relatorio.company_id.name,
            'total_balance': relatorio.total_balance,
            'create_date': relatorio.create_date.strftime('%Y-%m-%dT%H:%M:%S') if relatorio.create_date else None,
            'order_number': relatorio.order_number,
            'descricao': relatorio.descricao,
            'create_uid': relatorio.create_uid.name if relatorio.create_uid else None,
            'login': relatorio.create_uid.login if relatorio.create_uid else None,
            'subcontas': [
                {
                    'id': subconta.id,
                    'name': subconta.name,
                    'balance': subconta.balance,
                    'operation_type': subconta.operation_type,
                    'create_date': subconta.create_date.strftime('%Y-%m-%d'),
                    'items': [
                        {
                            'id': item.id,
                            'item_name': item.name,
                            'amount': item.amount,
                            'create_date': item.create_date.strftime('%Y'),
                        } for item in subconta.item_ids
                    ]
                } for subconta in relatorio.subconta_ids
            ]
        }

        return werkzeug.wrappers.Response(
            json.dumps(data),
            headers={'Content-Type': 'application/json'},
            status=200
        )

    @http.route('/report/subcontas', auth="none", methods=['GET'])
    def report_subcontas(self, **kw):
        table = request.env['relatorio.relatorio'].sudo().search([])
        data = []
        for subconta in table:
            data.append({
                'id': subconta.id,
                'name': subconta.name,
            })
        return werkzeug.wrappers.Response(json.dumps(data), headers={'Content-Type': 'application/json'}, status=200)

    @http.route('/report/odoo_users', auth='none', methods=['GET'])
    def list_odoo_users(self):
        table = request.env['res.users'].sudo().search([])

        info = []
        for user in table:
            info.append({
                'id': user.id,
                'name': user.name,
            })
        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)

    @http.route('/report/send', auth='none', type="json", methods=['POST'], csrf=False)
    def send_report(self, **kwargs):
        data = request.httprequest.json

        report_id = data.get('report_id')
        user_ids = data.get('user_ids')
        pdf_blob = data.get('pdf_blob')

        if not report_id or not user_ids or not pdf_blob:
            return "Faltando report_id, user_ids ou pdf_blob"

        pdf_data = base64.b64decode(pdf_blob)

        report = request.env['relatorio.relatorio'].sudo().browse(int(report_id))
        if not report:
            return "Relatório não encontrado"

        message_body = f"Relatório '{report.name}' foi enviado a você."

        for user_id in user_ids:
            request.env['mail.message'].sudo().create({
                'message_type': 'notification',
                'subtype_id': request.env.ref('mail.mt_comment').id,
                'body': message_body,
                'partner_ids': [(4, request.env['res.users'].browse(int(user_id)).partner_id.id)],
            })

        return "Relatório enviado com sucesso"

    @http.route('/report/odoo_company', auth='none', csrf=False, methods=['GET'])
    def list_odoo_company(self):
        table = request.env['res.company'].sudo().search([])
        info = []
        for user in table:
            info.append({
                'id': user.id,
                'name': user.name,
            })

        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)
