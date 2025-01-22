from odoo import http
from odoo.http import request


class Portalinherit(http.Controller):
    @http.route('/check_user_role', type='http', website=True )
    def check_user_role(self):
        try:
            if not request.env.user or not request.env.user.id:
                return {'error': 'Usuário não autenticado'}

            user = request.env.user
            logistica_group = request.env.ref('portalinherit.access_low_level_group')
            technician_group = request.env.ref('portalinherit.access_mid_level_group')
            responsible_group = request.env.ref('portalinherit.access_admin_level_group')

            is_portal = logistica_group.id in user.groups_id.ids
            is_tecnico = technician_group.id in user.groups_id.ids
            is_responsible = responsible_group.id in user.groups_id.ids

            print('is a portal',is_portal)
            print('is a tecnical',is_tecnico)
            print('is a responsible',is_responsible)


            # response_data = {
            #     'is_technician_resident': is_tecnico,
            #     'is_responsible': is_responsible,
            #     'is_portal': is_portal
            # }

            # return response_data

        except Exception as e:
            return {'error': str(e)}
