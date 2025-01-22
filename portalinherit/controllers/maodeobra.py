from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request


class WeblearnsPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        rtn = super(WeblearnsPortal, self)._prepare_home_portal_values(counters)
        user = request.env.user
        stock_picking_count = request.env['requisicaomaodeobra.requisicaomaodeobra'].sudo().search_count([
            ('create_uid', '=', user.id)
        ])
        rtn['maodeobra_counts'] = stock_picking_count

        return rtn


class YourController(http.Controller):

    @http.route('/requisicaomaodeobra', auth='user', type='http', website=True)
    def index(self, **kw):
        user = http.request.env.user
        action_values = {
            'name': 'Menu de Mao-de-obra',
            'type': 'ir.actions.act_window',
            'res_model': 'requisicaomaodeobra.requisicaomaodeobra',
            'view_mode': 'tree,form',
            'view_id': request.env.ref('requisicaomaodeobra.requisicaomaodeobra_tree_view').id,
        }
        action = request.env['ir.actions.act_window'].sudo().create(action_values)

        domain = [('create_uid', '=', user.id)]
        action['domain'] = domain

        action_id = action.id
        return request.redirect(
            '/web#cids=1&menu_id=108&action=%s&model=requisicaomaodeobra.requisicaomaodeobra&view_type=list' % (
                action_id))



