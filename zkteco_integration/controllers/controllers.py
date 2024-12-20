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
    class ZKTecoController(http.Controller):
        @http.route('/iclock/cdata', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
        def receive_records(self, **kwargs):
            if request.httprequest.method == 'POST':
                post_content = request.httprequest.data.decode('utf-8')

                sn = kwargs.get('SN')
                if not sn:
                    _logger.error("Número de serie (SN) no encontrado en la solicitud.")
                    return "Error: Número de serie no encontrado"

                _logger.info("Datos recibidos de ZKTeco: %s", post_content)

                machine = request.env['zk.machine'].sudo().search([('name', '=', sn)], limit=1)
                if not machine:
                    raise UserError(f'Máquina con SN {sn} no encontrada.')

                work_area = machine.address_id

                data_lines = post_content.splitlines()

                for line in data_lines:
                    fields = line.split('\t')

                    if len(fields) < 10:
                        _logger.warning(f"Datos incompletos en la línea: {line}")
                        continue

                    device_id = fields[0]
                    timestamp = fields[1]
                    punch_type = fields[2]
                    attendance_type = fields[3]

                    employee = request.env['hr.employee'].sudo().search([('device_id', '=', device_id)], limit=1)
                    if not employee:
                        _logger.warning(f"Empleado no encontrado para el device_id: {device_id}")
                        continue

                    try:
                        attendance_datetime = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        _logger.warning(f"Fecha y hora inválida en la línea: {line}")
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
                        _logger.info("Registrado Check In para empleado %s en %s", employee.name, attendance_datetime)

                        threading.Thread(target=self.send_to_relevant_websockets,
                                         args=(employee.id, attendance_datetime)).start()

                    elif punch_type == '1':
                        attendance = request.env['hr.attendance'].sudo().search([
                            ('employee_id', '=', employee.id),
                            ('check_out', '=', False)
                        ], order='check_in desc', limit=1)

                        if attendance:
                            attendance.sudo().write({'check_out': attendance_datetime})
                            _logger.info("Registrado Check Out para empleado %s en %s", employee.name,
                                         attendance_datetime)
                        else:
                            _logger.warning("No se encontró un Check In previo para el empleado %s.", employee.name)
                    else:
                        _logger.warning("Tipo de marcación no soportado: %s", punch_type)

            return http.Response("OK", status=200)

        def send_to_relevant_websockets(self, employee_id, attendance_datetime):
            formatted_datetime = attendance_datetime.strftime('%Y-%m-%d %H:%M:%S')

            message_data = {
                'employee_id': employee_id,
                'attendance_datetime': formatted_datetime,
                'status': 'Check In' if attendance_datetime else 'Check Out'
            }

            print(f"Enviando para RabbitMQ: {message_data}")
            self.send_message_to_websockets(message_data)

        def send_message_to_websockets(self, message_data):
            uri = "ws://localhost:8765"
            try:
                asyncio.run(self.send_message(uri, message_data))
            except Exception as e:
                print(f"Erro ao enviar mensagem via WebSocket: {e}")

        async def send_message(self, uri, message_data):
            async with websockets.connect(uri) as websocket:
                await websocket.send(str(message_data))

