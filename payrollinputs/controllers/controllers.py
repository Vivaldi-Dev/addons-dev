# -*- coding: utf-8 -*-
# from odoo import http


# class Payrollinputs(http.Controller):
#     @http.route('/payrollinputs/payrollinputs', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/payrollinputs/payrollinputs/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('payrollinputs.listing', {
#             'root': '/payrollinputs/payrollinputs',
#             'objects': http.request.env['payrollinputs.payrollinputs'].search([]),
#         })

#     @http.route('/payrollinputs/payrollinputs/objects/<model("payrollinputs.payrollinputs"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('payrollinputs.object', {
#             'object': obj
#         })
