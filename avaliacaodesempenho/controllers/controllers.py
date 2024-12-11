# -*- coding: utf-8 -*-
# from odoo import http


# class Avaliacaodesempenho(http.Controller):
#     @http.route('/avaliacaodesempenho/avaliacaodesempenho', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/avaliacaodesempenho/avaliacaodesempenho/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('avaliacaodesempenho.listing', {
#             'root': '/avaliacaodesempenho/avaliacaodesempenho',
#             'objects': http.request.env['avaliacaodesempenho.avaliacaodesempenho'].search([]),
#         })

#     @http.route('/avaliacaodesempenho/avaliacaodesempenho/objects/<model("avaliacaodesempenho.avaliacaodesempenho"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('avaliacaodesempenho.object', {
#             'object': obj
#         })
