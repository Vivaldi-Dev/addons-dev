# -*- coding: utf-8 -*-
# from odoo import http


# class HrAbsence(http.Controller):
#     @http.route('/hr_absence/hr_absence', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_absence/hr_absence/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_absence.listing', {
#             'root': '/hr_absence/hr_absence',
#             'objects': http.request.env['hr_absence.hr_absence'].search([]),
#         })

#     @http.route('/hr_absence/hr_absence/objects/<model("hr_absence.hr_absence"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_absence.object', {
#             'object': obj
#         })
