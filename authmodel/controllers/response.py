import json
from odoo import http
from odoo.http import request, Response, JsonRequest
from odoo.tools import date_utils


class JsonRequestNew(JsonRequest):
    def _json_response(self, result=None, error=None):
        if self.httprequest.path.startswith("/api/"):
            response = result if error is None else error
            mime = 'application/json'
            body = json.dumps(response, default=date_utils.json_default)
            return Response(
                body,
                status=error and error.pop('http_status', 200) or 200,
                headers=[('Content-Type', mime), ('Content-Length', len(body))]
            )
        return super(JsonRequestNew, self)._json_response(result=result, error=error)


class RootNew(http.Root):
    def get_request(self, httprequest):
        jsonResponse = super(RootNew, self).get_request(httprequest=httprequest)

        if httprequest.mimetype in ("application/json", "application/json-rpc"):
            return JsonRequestNew(httprequest)
        else:
            return jsonResponse


http.root = RootNew()


@http.route('/api/custom/response', auth='public', type='json', methods=['GET'])
def custom_response(self):
    try:
        data = {
            'message': 'Esta é uma resposta personalizada!',
            'status': 'success'
        }

        if not data:
            raise ValueError("Dados não encontrados")

        return data

    except Exception as e:
        return {'status': 'error', 'message': str(e)}
