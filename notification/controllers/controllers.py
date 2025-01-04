# -*- coding: utf-8 -*-
# from odoo import http


# class Notification(http.Controller):
#     @http.route('/notification/notification', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/notification/notification/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('notification.listing', {
#             'root': '/notification/notification',
#             'objects': http.request.env['notification.notification'].search([]),
#         })

#     @http.route('/notification/notification/objects/<model("notification.notification"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('notification.object', {
#             'object': obj
#         })
