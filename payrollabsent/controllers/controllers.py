# -*- coding: utf-8 -*-
# from odoo import http


# class Payrollabsent(http.Controller):
#     @http.route('/payrollabsent/payrollabsent', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/payrollabsent/payrollabsent/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('payrollabsent.listing', {
#             'root': '/payrollabsent/payrollabsent',
#             'objects': http.request.env['payrollabsent.payrollabsent'].search([]),
#         })

#     @http.route('/payrollabsent/payrollabsent/objects/<model("payrollabsent.payrollabsent"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('payrollabsent.object', {
#             'object': obj
#         })
