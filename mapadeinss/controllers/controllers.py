# -*- coding: utf-8 -*-
# from odoo import http


# class Mapadeinss(http.Controller):
#     @http.route('/mapadeinss/mapadeinss', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mapadeinss/mapadeinss/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mapadeinss.listing', {
#             'root': '/mapadeinss/mapadeinss',
#             'objects': http.request.env['mapadeinss.mapadeinss'].search([]),
#         })

#     @http.route('/mapadeinss/mapadeinss/objects/<model("mapadeinss.mapadeinss"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mapadeinss.object', {
#             'object': obj
#         })
