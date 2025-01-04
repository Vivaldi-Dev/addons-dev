import threading
import asyncio
import websockets
from odoo import http
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZKTecoController(http.Controller):
    @http.route('/iclock/cdata', auth='none', methods=['GET', 'POST'], csrf=False)
    def receive_records(self, **kwargs):
        if request.httprequest.method == 'POST':
            post_content = request.httprequest.data.decode('utf-8')
            sn = kwargs.get('SN')

            if not sn:
                _logger.error("Número de série (SN) não encontrado na solicitação.")
                return "Error: Número de série não encontrado"

            _logger.info("Dados recebidos de ZKTeco: %s", post_content)

            machine = request.env['zk.machine'].sudo().search([('name', '=', sn)], limit=1)
            if not machine:
                raise UserError(f'Máquina com SN {sn} não encontrada.')

            work_area = machine.address_id
            data_lines = post_content.splitlines()

            for line in data_lines:
                fields = line.split('\t')
                if len(fields) < 10:
                    _logger.warning(f"Dados incompletos na linha: {line}")
                    continue

                device_id, timestamp, punch_type, attendance_type = fields[0], fields[1], fields[2], fields[3]
                employee = request.env['hr.employee'].sudo().search([('device_id', '=', device_id)], limit=1)

                if not employee:
                    _logger.warning(f"Empregado não encontrado para o device_id: {device_id}")
                    continue

                try:
                    attendance_datetime = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    _logger.warning(f"Data e hora inválidas na linha: {line}")
                    continue

                if punch_type == '0':
                    websocket_record = request.env['hr.attendance'].sudo().create({
                        'employee_id': employee.id,
                        'check_in': attendance_datetime,
                        'punching_time': attendance_datetime,
                        'punch_type': punch_type,
                        'attendance_type': attendance_type,
                        'address_id': work_area.id,
                    })

                    notification = request.env['attendance.notification'].sudo().create({
                        'employee_id': employee.id,
                        'check_in': attendance_datetime,
                    })

                    _logger.info("Registrado Check In para empregado %s em %s", employee.name, attendance_datetime)

                    employee_id = employee.id
                    employee_name = employee.name
                    x_ativo = employee.x_ativo
                    formatted_datetime = attendance_datetime.strftime('%Y-%m-%d %H:%M:%S')

                    threading.Thread(target=self.send_to_relevant_websockets,
                                     args=(employee_id, x_ativo, formatted_datetime, employee_name)).start()

                elif punch_type == '1':
                    attendance = request.env['hr.attendance'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('check_out', '=', False)
                    ], order='check_in desc', limit=1)

                    notification = request.env['attendance.notification'].sudo().create({
                        'employee_id': employee.id,
                        'check_out': attendance_datetime,
                    })

                    if notification:

                        notification.sudo().write({
                            'check_out': attendance_datetime
                        })
                        _logger.info("Atualizado Check Out para o empregado %s em %s", employee.name,
                                     attendance_datetime)
                    else:
                        _logger.warning("Não foi encontrado um Notification para o empregado %s.", employee.name)

                    if attendance:
                        attendance.sudo().write({'check_out': attendance_datetime})
                        _logger.info("Registrado Check Out para empregado %s em %s", employee.name, attendance_datetime)
                    else:
                        _logger.warning("Não foi encontrado um Check In prévio para o empregado %s.", employee.name)
                else:
                    _logger.warning("Tipo de marcação não suportado: %s", punch_type)

        return http.Response("OK", status=200)

    def send_to_relevant_websockets(self, employee_id, x_ativo, attendance_datetime, employee_name):
        if x_ativo:
            message_data = {
                'employee_id': employee_id,
                'attendance_datetime': attendance_datetime,
                'status': 'Check In'
            }

            _logger.info(f"Enviando mensagem para o WebSocket: {message_data}")
            self.send_message_to_websockets(message_data)
        else:
            _logger.info(
                f"Notificação em tempo real desativada para o empregado {employee_name}. Nenhuma mensagem enviada.")

    def send_message_to_websockets(self, message_data):
        uri = "ws://localhost:8765"
        try:
            asyncio.run(self.send_message(uri, message_data))
        except Exception as e:
            _logger.error(f"Erro ao enviar mensagem via WebSocket: {e}")

    async def send_message(self, uri, message_data):
        async with websockets.connect(uri) as websocket:
            await websocket.send(str(message_data))
