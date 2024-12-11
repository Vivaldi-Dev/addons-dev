from . import controllers
from . import models
from . import decorators
from . import utils
# # -*- coding: utf-8 -*-
# import json
#
# import werkzeug
#
# from . import controllers
# from . import models
# from . import utils
# from . import decorators
# from odoo.http import JsonRequest, Response
# from .utils.urls import URL_API_BASE
# from odoo.tools import date_utils
# def __init__(self, *args):
#     super(JsonRequest, self).__init__(*args)
#
#     self.params = {}
#
#     args = self.httprequest.args
#     request = None
#     request_id = args.get('id')
#
#     request = self.httprequest.get_data().decode(self.httprequest.charset)
#     try:
#         self.jsonrequest = json.loads(request)
#     except ValueError:
#         if self.httprequest.method == 'GET':
#             self.jsonrequest = {}
#         else:
#             msg = 'Invalid JSON data tests: %r' % (request,)
#             raise werkzeug.exceptions.BadRequest(msg)
#
#     self.params = dict(self.jsonrequest.get("params", {}))
#     self.context = self.params.pop('context', dict(self.session.context))
#
#
# def _json_response(self, result=None, error=None):
#     print("Método _json_response chamado com:", result, error)
#     if str(self.httprequest.url).__contains__(URL_API_BASE):
#         # Formato customizado de resposta
#         response = error if error else result
#         status_code = int(error.get('http_status', '500')) if error else int(result.get('http_status', '200'))
#     else:
#         # Resposta padrão JSON-RPC
#         response = {
#             'jsonrpc': '2.0',
#             'id': self.jsonrequest.get('id'),
#             'result': result if result else None,
#             'error': error if error else None,
#         }
#         status_code = 200
#
#     mime = 'application/json'
#     body = json.dumps(response, default=date_utils.json_default)
#
#     return Response(
#         body, status=status_code,
#         headers=[('Content-Type', mime), ('Content-Length', len(body))]
#     )
#
#
# print("START CONFIGURATION Vivas")
# setattr(JsonRequest, '__init__', __init__)
# setattr(JsonRequest, '_json_response', _json_response)
#
#
# def __init__(self, *args):
#     print("[DEBUG] JsonRequest __init__ chamado")
#     super(JsonRequest, self).__init__(*args)
#
# def _json_response(self, result=None, error=None):
#     print("[DEBUG] _json_response chamado com:", result, error)
#     # Restante do código...
#
#
# def __init__(self, *args):
#     super(JsonRequest, self).__init__(*args)
#
#     self.jsonp_handler = None
#
#     args = self.httprequest.args
#     jsonp = args.get('jsonp')
#     self.jsonp = jsonp
#     request = None
#     request_id = args.get('id')
#
#     if jsonp and self.httprequest.method == 'POST':
#         # jsonp 2 steps step1 POST: save call
#         def handler():
#             self.session['jsonp_request_%s' % (request_id,)] = self.httprequest.form['r']
#             self.session.modified = True
#             headers = [('Content-Type', 'text/plain; charset=utf-8')]
#             r = werkzeug.wrappers.Response(request_id, headers=headers)
#             return r
#
#         self.jsonp_handler = handler
#         return
#     elif jsonp and args.get('r'):
#         request = args.get('r')
#     elif jsonp and request_id:
#         request = self.session.pop('jsonp_request_%s' % (request_id,), '{}')
#     else:
#         request = self.httprequest.stream.read()
#
#     try:
#         self.jsonrequest = json.loads(request)
#     except ValueError:
#         msg = 'Invalid JSON data: %r' % (request,)
#
#         raise werkzeug.exceptions.BadRequest(msg)
#
#     self.params = dict(self.jsonrequest.get("params", {}))
#     self.context = self.params.pop('context', dict(self.session.context))
#
#
#
#
# print("Método _json_response substituído com sucesso!")