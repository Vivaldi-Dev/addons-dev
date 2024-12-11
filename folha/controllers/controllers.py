# -*- coding: utf-8 -*-
# from odoo import http


# class Folha(http.Controller):
#     @http.route('/folha/folha', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/folha/folha/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('folha.listing', {
#             'root': '/folha/folha',
#             'objects': http.request.env['folha.folha'].search([]),
#         })

#     @http.route('/folha/folha/objects/<model("folha.folha"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('folha.object', {
#             'object': obj
#         })
