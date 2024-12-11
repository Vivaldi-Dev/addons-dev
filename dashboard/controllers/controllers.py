from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request


class WeblearnsPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        rtn = super(WeblearnsPortal, self)._prepare_home_portal_values(counters)
        user = request.env.user
        stock_picking_count = request.env['requisicaopagamento.requisicaopagamento'].sudo().search_count([
            ('create_uid', '=', user.id)
        ])
        rtn['pagamento_counts'] = stock_picking_count

        return rtn



