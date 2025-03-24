from odoo.http import request, Response

@http.route('/test', auth='public', methods=['POST'], type="json", csrf=False)
def recieve_data(self, **kw):
      headers = request.httprequest.headers
      args = request.httprequest.args
      data = request.jsonrequest
      Response.status = "401 unauthorized"
      return {'error' : 'You are not allowed to access the resource'}