# -*- coding: utf-8 -*-
# from odoo import http


# class EmployeeInherit(http.Controller):
#     @http.route('/employee_inherit/employee_inherit', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/employee_inherit/employee_inherit/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('employee_inherit.listing', {
#             'root': '/employee_inherit/employee_inherit',
#             'objects': http.request.env['employee_inherit.employee_inherit'].search([]),
#         })

#     @http.route('/employee_inherit/employee_inherit/objects/<model("employee_inherit.employee_inherit"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('employee_inherit.object', {
#             'object': obj
#         })
