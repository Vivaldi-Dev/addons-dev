import json
from functools import wraps
from odoo.http import request
from werkzeug.wrappers import Response

def token_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        token = request.httprequest.headers.get('Authorization')

        if not token:
            return Response(
                json.dumps({"status": "error", "message": "Access token não fornecido."}),
                status=401,
                content_type='application/json'
            )

        token = token.replace('Bearer ', '')
        valid_token = request.env['authmodel.authmodel'].sudo().search([('token', '=', token)], limit=1)

        if not valid_token:
            return Response(
                json.dumps({"status": "error", "message": "Token inválido ou expirado."}),
                status=401,
                content_type='application/json'
            )

        return func(self, *args, **kwargs)

    return wrapper
