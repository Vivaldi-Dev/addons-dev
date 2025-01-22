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

    @http.route("/api/auth/signIn", auth='none', type="json", methods=['POST'], csrf=False, cors='*')
    def api_logins(self):
        try:
            data = request.httprequest.data.decode()
            data = json.loads(data)

            print("Dados recebidos no login: %s", data)
        except (json.JSONDecodeError, AttributeError):
            return {"error": "O corpo da solicitação deve ser um JSON válido", "code": 400}

        if not data:
            return {"error": "O corpo da solicitação não pode estar vazio", "code": 400}

        username = data.get("username")
        password = data.get("password")

        if not username:
            return {"error": "O campo 'username' é obrigatório", "code": 403}

        if not password:
            return {"error": "O campo 'password' é obrigatório", "code": 403}

        db = request.env.cr.dbname

        try:
            request.session.authenticate(db, username, password)
        except AccessError as aee:
            return {"error": f"Erro de acesso: {aee.name}", "code": 403}
        except AccessDenied:
            return {"error": "Username ou senha incorretos! Por favor, digite dados corretos e tente novamente.",
                    "code": 403}
        except Exception as e:
            return {"error": f"Erro inesperado: {e}", "code": 500}

        uid = request.session.uid
        if not uid:
            return {"error": "Falha na autenticação", "code": 401}

        access_token_model = request.env["authmodel.authmodel"]
        access_token = access_token_model.find_or_create_token(user_id=uid, create=True)

        token_record = access_token_model.sudo().search([("user_id", "=", uid)], order="id DESC", limit=1)
        access_token_value = token_record.token if token_record else None
        refresh_token_value = token_record.refresh if token_record else None
        token_expiry_date = token_record.token_expiry_date if token_record else None
        refresh_expiry_date = token_record.refresh_expiry_date if token_record else None

        employee = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)

        employee_data = {
            "employee_id": employee.id if employee else "Nenhum funcionário encontrado",
            "employee_name": employee.name if employee else "Nenhum funcionário encontrado",
            "job_position": employee.job_id.name if employee and employee.job_id else "Sem cargo definido",
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
                "name": request.env.user.company_id.name or "Empresa não definida",
            },
            "company_ids": request.env.user.company_ids.ids if uid else [],
            "partner_id": request.env.user.partner_id.id,
            "company_name": {
                "id": request.env.user.company_id.id,
                "name": request.env.user.company_id.name or "Empresa não definida",
            },
            "country": {
                "id": request.env.user.country_id.id if request.env.user.country_id else "Nenhum país definido",
                "name": request.env.user.country_id.name or "Nenhum país definido",
            },
            "contact_address": request.env.user.contact_address or "Endereço não disponível",
            "employee": employee_data,
            "access_token": access_token_value,
            "refresh_token": refresh_token_value,
            "token_expiry_date": token_expiry_date,
            "refresh_expiry_date": refresh_expiry_date,
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
