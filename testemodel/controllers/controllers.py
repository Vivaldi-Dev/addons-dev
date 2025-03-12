# -*- coding: utf-8 -*-
# from odoo import http


# class Testemodel(http.Controller):
#     @http.route('/testemodel/testemodel', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/testemodel/testemodel/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('testemodel.listing', {
#             'root': '/testemodel/testemodel',
#             'objects': http.request.env['testemodel.testemodel'].search([]),
#         })

#     @http.route('/testemodel/testemodel/objects/<model("testemodel.testemodel"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('testemodel.object', {
#             'object': obj
#         })
