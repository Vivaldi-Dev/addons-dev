from odoo import http
from odoo.http import request


class Portalinherit(http.Controller):
    @http.route('/data/data/',  type='http', auth='public', website=True)
    def index(self, **kw):
        return request.render(
            "portalinherit.Dashboardvol", {})


class WebsiteForm(http.Controller):

    @http.route('/candidato/', type='http', auth='public', website=True)
    def index_page(self, **kw):
        return request.render('portalinherit.on_sucess_submit', {})