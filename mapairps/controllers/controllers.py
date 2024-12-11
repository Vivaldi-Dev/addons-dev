# -*- coding: utf-8 -*-
# from odoo import http


# class Mapairps(http.Controller):
#     @http.route('/mapairps/mapairps', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mapairps/mapairps/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mapairps.listing', {
#             'root': '/mapairps/mapairps',
#             'objects': http.request.env['mapairps.mapairps'].search([]),
#         })

#     @http.route('/mapairps/mapairps/objects/<model("mapairps.mapairps"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mapairps.object', {
#             'object': obj
#         })
