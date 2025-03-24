# -*- coding: utf-8 -*-
# from odoo import http


# class JsVersionPontual(http.Controller):
#     @http.route('/js_version_pontual/js_version_pontual', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/js_version_pontual/js_version_pontual/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('js_version_pontual.listing', {
#             'root': '/js_version_pontual/js_version_pontual',
#             'objects': http.request.env['js_version_pontual.js_version_pontual'].search([]),
#         })

#     @http.route('/js_version_pontual/js_version_pontual/objects/<model("js_version_pontual.js_version_pontual"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('js_version_pontual.object', {
#             'object': obj
#         })
