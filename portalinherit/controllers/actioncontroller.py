from odoo import http
from odoo.http import request

class CustomController(http.Controller):

    @http.route('/actionfilter', type='http', website=True)
    def _get_user_name(self):
        action_id = request.env.ref('portalinherit.action_test')
        print(action_id)
        if action_id:
            action = request.env['ir.actions.act_window'].sudo().browse(action_id.id)
            if action:



                return request.redirect('/web#cids=1&menu_id=108&action=%s&model=stock.picking&view_type=list' % (action.id))
            else:
                return "Action not found"
        else:
            return "Action ID not found"


