# -*- coding: utf-8 -*-
# from odoo import http


# class HrReports(http.Controller):
#     @http.route('/hr_reports/hr_reports', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_reports/hr_reports/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_reports.listing', {
#             'root': '/hr_reports/hr_reports',
#             'objects': http.request.env['hr_reports.hr_reports'].search([]),
#         })

#     @http.route('/hr_reports/hr_reports/objects/<model("hr_reports.hr_reports"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_reports.object', {
#             'object': obj
#         })
