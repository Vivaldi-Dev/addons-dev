from odoo import conf, http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class ProjectCustomerPortalInherit(CustomerPortal):

    @http.route(['/my/projects'], type='http', auth="user", website=True)
    def portal_my_projects(self, **kw):
            # user = http.request.env.user
            action_values = {
                'name': 'Projects',
                'type': 'ir.actions.act_window',
                'res_model': 'project.project',
                'view_mode': 'tree,form,kanban',
                'view_id': request.env.ref('project.view_project_kanban').id,
            }
            action = request.env['ir.actions.act_window'].sudo().create(action_values)
            #
            # domain = [('create_uid', '=', user.id)]
            # action['domain'] = domain

            action_id = action.id
            return request.redirect(
                '/web#cids=1&menu_id=108&action=%s&project.project&view_type=kanban' % (
                    action_id))


