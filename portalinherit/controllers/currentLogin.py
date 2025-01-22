from odoo import http
from odoo.http import request
import json


class CustomController(http.Controller):

    @http.route('/get_user_info', type='http', auth='user', website=True)
    def get_user_info(self):
        user = http.request.env.user
        user_login = user.login

        relevant_groups = ["Logistica", "Tecnico Resisdente", "Eg.Responsavel"]
        user_relevant_groups = [group for group in user.groups_id.mapped('name') if group in relevant_groups]

        if user_relevant_groups:
            message = "O usuario pertence ao seguintes grupos : {}".format(', '.join(user_relevant_groups))
        else:
            message = "O usuario nao pertence a nenhum dos grupos."

        response_data = {
            'user_id': user.id,
            'user_login': user_login,
            'relevant_groups': user_relevant_groups,
            'message': message
        }

        return json.dumps(response_data)


