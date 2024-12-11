# -*- coding: utf-8 -*-
import json
from pickle import FALSE

import werkzeug.wrappers
from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


class Newreport(http.Controller):
    @http.route('/newreport/newreport', auth='none', methods=["GET"])
    def index(self, **kw):

        prefixos_filtrados = ["3.1.1",
                              "3.1.2",
                              # "3.1.3",
                              ]

        dominio = []
        for prefixo in prefixos_filtrados:
            dominio.append(('code', 'like', prefixo + '%'))

        search_domain = ['|'] * (len(prefixos_filtrados) - 1) + dominio

        tableaccount = request.env['account.account'].sudo().search(search_domain)

        info = []
        for row in tableaccount:
            codigo_sem_pontos = row.code.replace('.', '')

            if codigo_sem_pontos.startswith('2'):
                continue

            for prefixo in prefixos_filtrados:
                if row.code.startswith(prefixo) and (len(row.code) == len(prefixo) or row.code[len(prefixo)] == '.'):
                    info.append({
                        'code': row.code,
                        'name': row.name,
                        'current_balance': row.current_balance,
                    })

                    break

        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)

    @http.route('/newreport/update', auth='none',type='json', csrf=False, methods=["PUT"])
    def newreport(self, **kwargs):

        data = request.jsonrequest
        current_balance_id = data.get('id')
        current_balance= data.get('balance')

        print(current_balance_id)
        print(current_balance)

        if not current_balance_id:
            return werkzeug.wrappers.Response(
                json.dumps({'error': 'Email is required'}, headers={'Content-Type': 'application/json'}), status=400)

        try:
            table = request.env['account.account'].sudo().search([('id', '=', current_balance_id)])

            if not table.exists():

                response_data={
                    'message': f"Current balance  with id {table} not found."
                }
                return werkzeug.wrappers.Response(json.dumps(response_data),headers={'Content-Type': 'application/json'},status=404)

            update_values = {}

            if current_balance is not None:
                update_values = {'current_balance': 5000}

                table.write(update_values)

            return werkzeug.wrappers.Response(json.dumps(update_values), headers={'Content-Type': 'application/json'}, status=200)

        except ValidationError as e:
            response_data = {
                'error': str(e),
            }
            return request.make_response(json.dumps(response_data), headers={'Content-Type': 'application/json'},
                                         status=400)










