# -*- coding: utf-8 -*-
# from odoo import http


# class Dashgraph(http.Controller):
#     @http.route('/dashgraph/dashgraph', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dashgraph/dashgraph/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dashgraph.listing', {
#             'root': '/dashgraph/dashgraph',
#             'objects': http.request.env['dashgraph.dashgraph'].search([]),
#         })

#     @http.route('/dashgraph/dashgraph/objects/<model("dashgraph.dashgraph"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dashgraph.object', {
#             'object': obj
#         })
