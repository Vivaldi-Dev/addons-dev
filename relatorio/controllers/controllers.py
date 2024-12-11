# -*- coding: utf-8 -*-
from odoo import http


class Relatorio(http.Controller):
    @http.route('/qweb-render', type='http', auth='public',website=True)
    def index(self, **kw):
        return http.request.render('relatorio.templateId')


