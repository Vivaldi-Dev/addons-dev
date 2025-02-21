# -*- coding: utf-8 -*-
# from odoo import http


# class DashboardPontual(http.Controller):
#     @http.route('/dashboard_pontual/dashboard_pontual', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dashboard_pontual/dashboard_pontual/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dashboard_pontual.listing', {
#             'root': '/dashboard_pontual/dashboard_pontual',
#             'objects': http.request.env['dashboard_pontual.dashboard_pontual'].search([]),
#         })

#     @http.route('/dashboard_pontual/dashboard_pontual/objects/<model("dashboard_pontual.dashboard_pontual"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dashboard_pontual.object', {
#             'object': obj
#         })
