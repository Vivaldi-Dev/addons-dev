# -*- coding: utf-8 -*-
# from odoo import http


# class PontualJs(http.Controller):
#     @http.route('/pontual_js/pontual_js', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pontual_js/pontual_js/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pontual_js.listing', {
#             'root': '/pontual_js/pontual_js',
#             'objects': http.request.env['pontual_js.pontual_js'].search([]),
#         })

#     @http.route('/pontual_js/pontual_js/objects/<model("pontual_js.pontual_js"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pontual_js.object', {
#             'object': obj
#         })
