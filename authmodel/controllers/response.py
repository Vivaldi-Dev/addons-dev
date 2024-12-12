import json
from odoo import http
from odoo.http import request, Response, JsonRequest
from odoo.tools import date_utils


class JsonRequestNew(JsonRequest):
    def _json_response(self, result=None, error=None):
        # Aplica a personalização apenas para rotas que começam com "/api/v1"
        if self.httprequest.path.startswith("/api/v1"):
            response = result if error is None else error
            mime = 'application/json'
            body = json.dumps(response, default=date_utils.json_default)
            return Response(
                body,
                status=error and error.pop('http_status', 200) or 200,
                headers=[('Content-Type', mime), ('Content-Length', len(body))]
            )
        # Caso contrário, usa o comportamento padrão
        return super(JsonRequestNew, self)._json_response(result=result, error=error)


class RootNew(http.Root):
    # Personalizando o método de solicitação para usar o JsonRequestNew
    def get_request(self, httprequest):
        jsonResponse = super(RootNew, self).get_request(httprequest=httprequest)

        if httprequest.mimetype in ("application/json", "application/json-rpc"):
            return JsonRequestNew(httprequest)
        else:
            return jsonResponse


# Substituindo o root do Odoo com o customizado
http.root = RootNew()


@http.route('/api/v1/custom/response', auth='public', type='json', methods=['GET'])
def custom_response(self):
    try:
        data = {
            'message': 'Esta é uma resposta personalizada!',
            'status': 'success'
        }
        # Garantir que a resposta contenha todos os dados necessários
        if not data:
            raise ValueError("Dados não encontrados")

        return data

    except Exception as e:
        return {'status': 'error', 'message': str(e)}