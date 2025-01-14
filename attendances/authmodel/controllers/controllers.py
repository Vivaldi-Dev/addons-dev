import json

from odoo import http
from odoo.http import request
from ..utils import *
from .decorators import token_required
from odoo.exceptions import AccessDenied, AccessError
from .decorators import override_json_response
import werkzeug
from datetime import datetime, timedelta


class Authmodel(http.Controller):

    # @http.route('/auth/signIn', auth='none', type="json", methods=['POST'], csrf=False, cors='*')
    # def sign_in(self):
    #     data = request.jsonrequest
    #
    #     username = data.get('username')
    #     password = data.get('password')
    #
    #     if not username or not password:
    #         return {
    #             "status": "error",
    #             "message": "Username ou password não foram fornecidos."
    #         }
    #
    #     TABLE_USER = request.env['res.users']
    #     user = TABLE_USER.sudo().search([("login", "=", username)], limit=1)
    #
    #     if not user:
    #         return {
    #             "status": "error",
    #             "message": "Usuário não encontrado."
    #         }
    #
    #     user_password = TABLE_USER.sudo().search([("password", "=", password)], limit=1)
    #
    #     if not user_password:
    #         return {
    #             "status": "error",
    #             "message": "Credenciais inválidas."
    #         }
    #
    #     access_token = request.env['authmodel.authmodel'].sudo().find_or_create_token(user_id=user.id, create=True)
    #
    #     if not access_token:
    #         return {
    #             "status": "error",
    #             "message": "Não foi possível gerar o token de acesso."
    #         }
    #
    #     refresh_token = request.env['authmodel.authmodel'].sudo().find_or_create_token(user_id=user.id, create=True)
    #
    #     if not refresh_token:
    #         return {
    #             "status": "error",
    #             "message": "Não foi possível gerar o refresh token."
    #         }
    #
    #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
    #
    #     employee_data = {
    #         "employee_id": employee.id if employee else None,
    #         "employee_name": employee.name if employee else None,
    #         "job_position": employee.job_id.name if employee and employee.job_id else None,
    #         "department": employee.department_id.name if employee and employee.department_id else None,
    #         "work_phone": employee.work_phone if employee else None,
    #         "work_email": employee.work_email if employee else None,
    #     }
    #
    #     return DlinkHelper.JsonValidResponse({
    #         "user": {
    #             "id": user.id,
    #             "name": user.name,
    #             "email": user.email,
    #             "login": user.login,
    #             "active": user.active,
    #         },
    #         "company_name": {
    #             "id": user.company_id.id,
    #             "name": user.company_id.name,
    #         },
    #         "country": {
    #             "id": request.env.user.country_id.id,
    #             "name": user.country_id.name,
    #         },
    #         "contact_address": user.contact_address,
    #
    #         "employee": employee_data,
    #
    #         "access_token": access_token.token,
    #         "refresh_token": refresh_token.refresh,
    #     })

    @http.route("/api/auth/signIn", auth='none', type="json", methods=['POST'], csrf=False, cors='*')
    def api_logins(self):
        data = request.httprequest.data.decode()
        data = json.loads(data)

        if not data:
            return {"error": "O corpo da solicitação deve ser um JSON válido", "code": 400}

        username = data.get("username")
        password = data.get("password")

        if not (username and password):
            return {"error": "Tanto o login quanto a senha são necessários no corpo da solicitação", "code": 403}

        db = request.env.cr.dbname

        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            return request.make_response("Access error", f"Error: {aee.name}", 403)
        except AccessDenied as ade:
            return {"error": "Username ou senha incorretos! Por favor, digite dados corretos e tente novamente.",
                    "code": 403}
        except Exception as e:
            info = f"The database name is not valid: {e}"
            return request.make_response("invalid_database", "Invalid database name", 403)

        uid = request.session.uid

        if not uid:
            return request.make_response("authentication_failed", "Authentication failed", 401)

        access_token_model = request.env["authmodel.authmodel"]
        access_token = access_token_model.find_or_create_token(user_id=uid, create=True)


        token_record = access_token_model.sudo().search([("user_id", "=", uid)], order="id DESC", limit=1)

        access_token_value = token_record.token if token_record else None
        refresh_token_value = token_record.refresh if token_record else None


        employee = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)

        employee_data = {
            "employee_id": employee.id if employee else None,
            "employee_name": employee.name if employee else None,
            "job_position": employee.job_id.name if employee and employee.job_id else None,

        }

        return {
            "user": {
                "id": request.env.user.id,
                "name": request.env.user.name,
                "email": request.env.user.login,
                "active": request.env.user.active,
            },
            "user_context": request.session.get_context() if uid else {},
            "company_id": {
                "id": request.env.user.company_id.id,
                "name": request.env.user.company_name,
            },
            "company_ids": request.env.user.company_ids.ids if uid else None,
            "partner_id": request.env.user.partner_id.id,
            "company_name": {
                "id": request.env.user.company_id.id,
                "name": request.env.user.company_name,
            },
            "country": {
                "id": request.env.user.country_id.id,
                "name": request.env.user.country_id.name,
            },
            "contact_address": request.env.user.contact_address,
            "employee": employee_data ,
            "access_token": access_token_value,
            "refresh_token": refresh_token_value,
        }

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
