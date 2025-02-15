# -*- coding: utf-8 -*-
# from odoo import http


# class EmployeeAbsents(http.Controller):
#     @http.route('/employee_absents/employee_absents', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/employee_absents/employee_absents/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('employee_absents.listing', {
#             'root': '/employee_absents/employee_absents',
#             'objects': http.request.env['employee_absents.employee_absents'].search([]),
#         })

#     @http.route('/employee_absents/employee_absents/objects/<model("employee_absents.employee_absents"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('employee_absents.object', {
#             'object': obj
#         })
