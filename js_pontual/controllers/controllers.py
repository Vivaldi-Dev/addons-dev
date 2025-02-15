# -*- coding: utf-8 -*-
# from odoo import http


# class JsPontual(http.Controller):
#     @http.route('/js_pontual/js_pontual', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/js_pontual/js_pontual/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('js_pontual.listing', {
#             'root': '/js_pontual/js_pontual',
#             'objects': http.request.env['js_pontual.js_pontual'].search([]),
#         })

#     @http.route('/js_pontual/js_pontual/objects/<model("js_pontual.js_pontual"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('js_pontual.object', {
#             'object': obj
#         })
