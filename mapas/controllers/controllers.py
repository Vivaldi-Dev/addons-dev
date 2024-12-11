# -*- coding: utf-8 -*-
# from odoo import http


# class Mapas(http.Controller):
#     @http.route('/mapas/mapas', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mapas/mapas/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mapas.listing', {
#             'root': '/mapas/mapas',
#             'objects': http.request.env['mapas.mapas'].search([]),
#         })

#     @http.route('/mapas/mapas/objects/<model("mapas.mapas"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mapas.object', {
#             'object': obj
#         })
