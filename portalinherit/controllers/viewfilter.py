from odoo import http
from odoo.http import request


class StockPickingController(http.Controller):

    @http.route('/filtered_stock_picking', type='http', auth='public', website=True)
    def filtered_stock_picking(self):
        try:
            # Obtém o usuário logado
            user = request.env.user

            # Filtra os registros de stock.picking com base no usuário logado
            stock_pickings = request.env['stock.picking'].sudo().search([('user_id', '=', user.id)])

            for picking in stock_pickings:
                print("Picking ID:", picking.id)
                print("Picking Name:", picking.name)

            return [{
                'id': picking.id,
                'name': picking.name,
                # Adicione outros campos que deseja retornar aqui
            } for picking in stock_pickings]

        except Exception as e:
            # Retorna um erro em caso de exceção
            return {'error': str(e)}

