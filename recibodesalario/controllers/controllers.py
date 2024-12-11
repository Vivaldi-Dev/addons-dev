# -*- coding: utf-8 -*-
# from odoo import http


# class Recibodesalario(http.Controller):
#     @http.route('/recibodesalario/recibodesalario', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/recibodesalario/recibodesalario/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('recibodesalario.listing', {
#             'root': '/recibodesalario/recibodesalario',
#             'objects': http.request.env['recibodesalario.recibodesalario'].search([]),
#         })

#     @http.route('/recibodesalario/recibodesalario/objects/<model("recibodesalario.recibodesalario"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('recibodesalario.object', {
#             'object': obj
#         })
