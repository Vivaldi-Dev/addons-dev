# -*- coding: utf-8 -*-
# from odoo import http


# class Recibodesalario(http.Controller):
#     @http.route('/js_reports_recibo/js_reports_recibo', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/js_reports_recibo/js_reports_recibo/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('js_reports_recibo.listing', {
#             'root': '/js_reports_recibo/js_reports_recibo',
#             'objects': http.request.env['js_reports_recibo.js_reports_recibo'].search([]),
#         })

#     @http.route('/js_reports_recibo/js_reports_recibo/objects/<model("js_reports_recibo.js_reports_recibo"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('js_reports_recibo.object', {
#             'object': obj
#         })
