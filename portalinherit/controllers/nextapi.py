# from odoo import http
from odoo import http
from odoo.http import request
import json
from odoo import fields


class NextController(http.Controller):

    @http.route('/dashbord_api/', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def list_material_requisitions(self, **kw):


            # Obter requisicoes com estados 'confirmed' ou 'assigned'
            requisitions = request.env['stock.picking'].sudo().search([('state', 'in', ['confirmed', 'assigned'])])
            data = []
            for requisition in requisitions:
                # Traduzir o estado para um formato desejado
                status = 'waiting' if requisition.state == 'confirmed' else 'ready' if requisition.state == 'assigned' else requisition.state
                # Obter os engenheiros responsáveis como uma lista de nomes
                responsible_users = [user.name for user in
                                     requisition.responsavel_user] if requisition.responsavel_user else []
                picking_data = {
                    'id': requisition.id,
                    'name': requisition.name,
                    'status': status,
                    'date': requisition.scheduled_date.strftime(fields.DATETIME_FORMAT),
                    'project': requisition.construnction_pro_id.name,
                    'task': requisition.job_orders_id.name,
                    "total_requisitions": len(requisitions),
                    'tecnico_residente': requisition.create_uid.name if requisition.create_uid else '',
                    'engenheiros_responsaveis': responsible_users,
                }
                data.append(picking_data)

            return json.dumps(data)

