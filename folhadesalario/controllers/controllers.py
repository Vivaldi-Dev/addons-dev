# -*- coding: utf-8 -*-
# from odoo import http


# class Folhapagamento(http.Controller):
#     @http.route('/folhadesalario/folhadesalario', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/folhadesalario/folhadesalario/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('folhadesalario.listing', {
#             'root': '/folhadesalario/folhadesalario',
#             'objects': http.request.env['folhadesalario.folhadesalario'].search([]),
#         })

#     @http.route('/folhadesalario/folhadesalario/objects/<model("folhadesalario.folhadesalario"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('folhadesalario.object', {
#             'object': obj
#         })
