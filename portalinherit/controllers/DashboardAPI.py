# from odoo import http
from odoo import http
from odoo.http import request
import datetime


class DashboardController(http.Controller):

    @http.route('/banco_teste/', auth='public', csrf=False, type='json', methods=['POST'])
    def list_material_requisitions(self, **kw):

        try:

            requisitions = request.env['stock.picking'].sudo().search([('state', 'in', ['confirmed', 'assigned'])])
            data = []
            for requisition in requisitions:

                status = 'waiting' if requisition.state == 'confirmed' else 'ready' if requisition.state == 'assigned' else requisition.state

                responsible_users = [user.name for user in
                                     requisition.responsavel_user] if requisition.responsavel_user else []
                picking_data = {
                    'id': requisition.id,
                    'name': requisition.name,
                    'status': status,
                    'date': requisition.scheduled_date,
                    'project': requisition.construnction_pro_id.name,
                    'task': requisition.job_orders_id.name,
                    "total_requisitions": len(requisitions),
                    'tecnico_residente': requisition.create_uid.name if requisition.create_uid else '',
                    'engenheiros_responsaveis': responsible_users,
                }
                data.append(picking_data)

            response = {
                "data": data, "total_requisitions": len(requisitions),
                "message": "Dados encontrados com sucesso" if requisitions else "Nenhum dado encontrado com os estados 'confirmed' ou 'assigned'",
                "success": True
            }
            return response

        except Exception as e:
            error_response = {"error": str(e), "message": "Erro ao processar a solicitação", "success": False
                              }
            return error_response
