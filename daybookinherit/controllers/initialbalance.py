from odoo import http
from odoo.http import request
import json

class DayBookController(http.Controller):

    @http.route('/day_book/saldo_inicial', auth='public', csrf=False, type='json', methods=['POST'])
    def get_saldo_inicial(self):

        last_record = request.env['day_book.day_book'].search([], order='create_date desc', limit=1)
        if last_record:
            saldo_inicial = last_record.saldo_inicial
            return {'saldo_inicial': saldo_inicial}
        else:
            return {'error': 'No records found'}

