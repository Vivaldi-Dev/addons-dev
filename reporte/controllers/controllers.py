# -*- coding: utf-8 -*-
import json
import werkzeug.wrappers
from odoo import http
from odoo.http import request
from datetime import datetime

class Reporte(http.Controller):

    @http.route('/tipo/recita', auth='none', methods=["GET"])
    def tipo_receita(self, **kw):

        prefixos_filtrados = ["3.1.1", "3.1.2", "3.1.3", ]
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
                        'id': row.id,
                        'name': row.name,
                    })

                    break

        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)

    @http.route('/subitems/report', auth='none', methods=["GET"])
    def subtipo(self, **kw):

        prefixos_filtrados = ["3.1.1", "3.1.2", "3.1.3", ]

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

    @http.route('/getById/<id>', auth='none', csrf=False, methods=["GET"])
    def getById(self, id, **kwargs):

        if not id:
            return werkzeug.wrappers.Response(
                json.dumps({'error': 'id is required'}, headers={'Content-Type': 'application/json'}), status=400)

        table = request.env['account.account'].sudo().search([('id', '=', id)])
        if not table:
            return werkzeug.wrappers.Response(
                json.dumps({'error': 'no such table'}, headers={'Content-Type': 'application/json'}), status=404)

        info = []
        for row in table:
            info.append({
                'code': row.code,
                'name': row.name,
                'current_balance': row.current_balance,
            })
        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)

    # @http.route('/subcontas', auth='none', csrf=False, methods=["GET"])
    # def get_by_id(self, **kwargs):
    #
    #     subcontas = request.env['subconta.subconta'].sudo().search([])
    #     data = []
    #
    #     for subconta in subcontas:
    #         items = [{'name': item.name, 'amount': item.amount} for item in subconta.item_ids]
    #         data.append({
    #             'name': subconta.name,
    #             'balance': subconta.balance,
    #             'Conta-mae': subconta.account_id.name,
    #             'item_ids': items,
    #         })
    #
    #     return werkzeug.wrappers.Response(json.dumps(data), headers={'Content-Type': 'application/json'}, status=200)

    @http.route('/subcontas/<int:id>', auth='none', methods=["GET"], type='http')
    def get_subcontas(self, id, **kwargs):
        """
        Retorna as subcontas associadas à conta mãe (account) com o ID fornecido.
        :param id: ID da conta mãe (account)
        :return: JSON com as subcontas e seus detalhes
        """

        account = request.env['account.account'].sudo().search([('id', '=', id)], limit=1)

        if not account:
            return werkzeug.wrappers.Response(
                json.dumps({'error': 'Conta mãe não encontrada'}),
                content_type='application/json',
                status=404
            )

        subcontas = account.subconta_ids

        subcontas_data = []
        for subconta in subcontas:
            subcontas_data.append({
                'id': subconta.id,
                'name': subconta.name,
                'operation_type': subconta.operation_type,
                'balance': subconta.balance,
                # 'parent_account_balance': subconta.parent_account_balance,
                'items': [{'id':item.id,'item_name': item.name, 'amount': item.amount} for item in subconta.item_ids],
            })


        return werkzeug.wrappers.Response(json.dumps(subcontas_data),content_type='application/json',status=200)
