import threading
import asyncio

import pytz
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
                return "Error: Máquina com SN não encontrada"

            work_area = machine.address_id
            data_lines = post_content.splitlines()

            maputo_tz = pytz.timezone("Africa/Maputo")
            utc_tz = pytz.utc

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
                    # print(f"Recebendo timestamp original da máquina: {timestamp}")


                    attendance_datetime = maputo_tz.localize(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'))

                    attendance_datetime_utc = attendance_datetime.astimezone(utc_tz).replace(tzinfo=None)

                    # print(f"Timestamp convertido para datetime (UTC naive): {attendance_datetime_utc}")

                except ValueError:
                    _logger.warning(f"Data e hora inválidas na linha: {line}")
                    continue

                if punch_type == '0':
                    print(f"Registrando Check In para {employee.name} às {attendance_datetime_utc}")

                    request.env['hr.attendance'].sudo().create({
                        'employee_id': employee.id,
                        'check_in': attendance_datetime_utc,
                        'punching_time': attendance_datetime_utc,
                        'punch_type': punch_type,
                        'attendance_type': attendance_type,
                        'address_id': work_area.id,
                    })

                    if employee.x_ativo:
                        print(f"Criando notificação de Check In para {employee.name} às {attendance_datetime_utc}")

                        request.env['attendance.notification'].sudo().create({
                            'employee_id': employee.id,
                            'check_in': attendance_datetime_utc,
                        })

                        threading.Thread(target=self.send_to_relevant_websockets,
                                         args=(employee.id, employee.x_ativo,
                                               attendance_datetime_utc.strftime('%Y-%m-%d %H:%M:%S'),
                                               employee.name)).start()
                    else:
                        _logger.info(
                            f"Check In registrado, mas nenhuma notificação criada para {employee.name} porque x_ativo está False."
                        )

                elif punch_type == '1':
                    print(f"Registrando Check Out para {employee.name} às {attendance_datetime_utc}")

                    notification = request.env['attendance.notification'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('check_out', '=', False)
                    ], order='check_in desc', limit=1)

                    if notification:

                        notification.sudo().write({'check_out': attendance_datetime_utc})
                        # print(f"Check Out atualizado na notificação de {employee.name} às {attendance_datetime_utc}")
                    else:
                        _logger.warning(f"Nenhuma notificação de Check In encontrada para {employee.name}.")


                    attendance = request.env['hr.attendance'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('check_out', '=', False)
                    ], order='check_in desc', limit=1)

                    if attendance:

                        attendance.sudo().write({'check_out': attendance_datetime_utc})
                        _logger.info(f"Check Out registrado para {employee.name} às {attendance_datetime_utc}")
                        # print(f"Check Out registrado para {employee.name} às {attendance_datetime_utc}")
                    else:
                        _logger.warning(f"Nenhum registro de Check In encontrado para {employee.name}.")
                else:
                    _logger.warning(f"Tipo de marcação não suportado: {punch_type}")

        return http.Response("OK", status=200)

    def send_to_relevant_websockets(self, employee_id, x_ativo, attendance_datetime, employee_name):
        if x_ativo:
            message_data = {
                'employee_id': employee_id,
                'attendance_datetime': attendance_datetime,
                'status': 'Check In',
                'employee_name': employee_name,
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
