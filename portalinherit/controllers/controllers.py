# # -*- coding: utf-8 -*-
# from odoo import http
#
#
# class Portalinherit(http.Controller):
#     @http.route('/portalinherit/portalinherit', auth='public')
#     def index(self, **kw):
#         return "Hello, world"
#
#     @http.route('/portalinherit/portalinherit/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('portalinherit.listing', {
#             'root': '/portalinherit/portalinherit',
#             'objects': http.request.env['portalinherit.portalinherit'].search([]),
#         })
#
#     @http.route('/portalinherit/portalinherit/objects/<model("portalinherit.portalinherit"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('portalinherit.object', {
#             'object': obj
#         })
