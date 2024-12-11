import json

from odoo import http
from odoo.http import request
from ..utils import *
from .decorators import token_required
from .decorators import override_json_response
import werkzeug
from datetime import datetime, timedelta


class Authmodel(http.Controller):

    @http.route('/auth/signIn', auth='none', type="json", methods=['POST'], csrf=False, cors='*')
    def sign_in(self):
        data = request.jsonrequest

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {
                "status": "error",
                "message": "Username ou password não foram fornecidos."
            }

        TABLE_USER = request.env['res.users']
        user = TABLE_USER.sudo().search([("login", "=", username)], limit=1)

        if not user:
            return {
                "status": "error",
                "message": "Usuário não encontrado."
            }

        TABLE_USER = request.env['res.users']
        user_password = TABLE_USER.sudo().search([("password", "=", password)], limit=1)

        if not user_password:
            return {
                "status": "error",
                "message": "Credenciais inválidas."
            }

        access_token = request.env['authmodel.authmodel'].sudo().find_or_create_token(user_id=user.id, create=True)

        if not access_token:
            return {
                "status": "error",
                "message": "Não foi possível gerar o token de acesso."
            }

        refresh_token = request.env['authmodel.authmodel'].sudo().find_or_create_token(user_id=user.id, create=True)

        if not refresh_token:
            return {
                "status": "error",
                "message": "Não foi possível gerar o refresh token."
            }

        return DlinkHelper.JsonValidResponse({

            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "login": user.login,
                "active": user.active,
            },

            "company_name": {
                "id": user.company_id.id,
                "name": user.company_name,
            },
            "country": {
                "id": request.env.user.country_id.id,
                "name": user.country_id.name,
            },
            "contact_address": user.contact_address,

            "access_token": access_token.token,
            "refresh_token": refresh_token.refresh,

        })

    @token_required
    @http.route("/auth/logout", methods=["POST"], auth="none", csrf=False)
    def logout(self):
            access_token = request.httprequest.headers.get("Authorization")

            if access_token and access_token.startswith("Bearer "):
                token = access_token[7:]

                access_token_model = request.env["authmodel.authmodel"].sudo()
                access_token_data = access_token_model.search([("token", "=", token)], limit=1)

                if access_token_data:
                    access_token_data.unlink()

            request.session.logout()

            request.uid = request.session.uid = None

            return werkzeug.wrappers.Response(
                response=json.dumps({
                    "status": "success",
                    "message": "Logged out successfully"
                }),
                status=200,
                headers=[('Content-Type', 'application/json')]
            )

    @token_required
    @http.route('/auth/protected', auth='none', methods=['GET'], csrf=False, cors='*')
    def protected_resource(self):
        return werkzeug.wrappers.Response(
            json.dumps({"status": "success",
                        "message": "Acesso autorizado ao recurso protegido!"})
        )
