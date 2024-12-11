import json
import werkzeug.wrappers
from odoo import http
from odoo.http import request


class fecthdata_report(http.Controller):

    @http.route('/report/fecthdata', auth='none', methods=['GET'])
    def report_fecthdata(self, **kw):
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
                        'name': row.name,
                    })
                    break

        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)

    @http.route('/subitems/fecthdata', auth='none', methods=['GET'])
    def subitems_fecthdata(self, **kw):
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
                        'name': row.name,
                    })

                    break

        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)

    @http.route('/items/fecthdata', auth='none', methods=["GET"])
    def index(self, **kw):

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
