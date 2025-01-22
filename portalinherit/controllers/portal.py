from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request


class WeblearnsPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        rtn = super(WeblearnsPortal, self)._prepare_home_portal_values(counters)
        user = request.env.user
        stock_picking_count = request.env['stock.picking'].sudo().search_count([
            ('create_uid', '=', user.id)
        ])
        rtn['student_counts'] = stock_picking_count
        return rtn



# class YourController(http.Controller):
#
#     @http.route('/redirect_to_picking_tree', type='http', auth='public')
#     def redirect_to_picking_tree(self):
#
#         user_id = request.env.user.id
#
#
#         return request.redirect(
#             '/web#cids=1&menu_id=109&action=487&model=stock.picking&view_type=list&domain=[("user_id", "=", %s)]' % user_id)
#
class YourController(http.Controller):

    @http.route('/jstech_test', auth='user', type='http', website=True)
    def index(self, **kw):
        user = http.request.env.user
        action_values = {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_id': request.env.ref('stock.vpicktree').id,
        }
        action = request.env['ir.actions.act_window'].sudo().create(action_values)

        if user.has_group('portalinherit.access_admin_level_group'):
            domain = ['|', ('create_uid', '=', user.id), ('responsavel_user', '=', user.id)]
            action['domain'] = domain
        elif user.has_group('portalinherit.access_mid_level_group'):
            domain = ['|', ('create_uid', '=', user.id), ('tecnico_user', '=', user.id)]

            action['domain'] = domain
        # Obtener el ID de la acción creada
        action_id = action.id

        return request.redirect('/web#cids=1&menu_id=108&action=%s&model=stock.picking&view_type=list' % (action_id))
