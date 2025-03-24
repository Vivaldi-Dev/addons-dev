import threading
import asyncio
import pytz
import websockets
from odoo import http
from datetime import datetime
import logging
from odoo.http import request

_logger = logging.getLogger(__name__)


class ZKTecoController(http.Controller):

    @http.route('/iclock/cdata', auth='none', methods=['GET', 'POST'], csrf=False)
    def receive_records(self, **kwargs):
        try:
            if request.httprequest.method == 'POST':
                post_content = request.httprequest.data.decode('utf-8')
                sn = request.params.get('SN')

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

                    # Definir notify_ids aqui, para que esteja disponível tanto para Check-in quanto para Check-out
                    notify_ids = employee.notify_employee_ids.mapped('id')

                    try:
                        attendance_datetime = maputo_tz.localize(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'))
                        attendance_datetime_utc = attendance_datetime.astimezone(utc_tz).replace(tzinfo=None)
                    except ValueError as e:
                        _logger.warning(f"Data e hora inválidas na linha: {line}. Erro: {e}")
                        continue

                    today_start = attendance_datetime_utc.replace(hour=0, minute=0, second=0)
                    today_end = attendance_datetime_utc.replace(hour=23, minute=59, second=59)

                    if punch_type == '0':  # Check-in
                        existing_checkin = request.env['hr.attendance'].sudo().search([
                            ('employee_id', '=', employee.id),
                            ('check_in', '>=', today_start),
                            ('check_in', '<=', today_end)
                        ], order='check_in asc', limit=1)

                        if existing_checkin:
                            _logger.info(f"Check-in já registrado para {employee.name} hoje, ignorando novo check-in.")
                            continue

                        attendance = request.env['hr.attendance'].sudo().create({
                            'employee_id': employee.id,
                            'check_in': attendance_datetime_utc,
                            'punching_time': attendance_datetime_utc,
                            'punch_type': punch_type,
                            'attendance_type': attendance_type,
                            'address_id': work_area.id,
                        })

                        if notify_ids:
                            _logger.info(
                                f"Criando notificação de Check In para {employee.name} às {attendance_datetime_utc}")
                            request.env['attendance.notification'].sudo().create({
                                'employee_id': employee.id,
                                'check_in': attendance_datetime_utc,
                            })

                            threading.Thread(target=self.send_to_relevant_websockets,
                                             args=(employee.id,
                                                   attendance_datetime_utc.strftime('%Y-%m-%d %H:%M:%S'),
                                                   employee.name,
                                                   'check-in',
                                                   notify_ids)).start()
                        else:
                            _logger.info(
                                f"Check In registrado, mas nenhuma notificação criada para {employee.name} porque não há funcionários a notificar.")

                    elif punch_type == '1':  # Check-out
                        _logger.info(f"Registrando Check Out para {employee.name} às {attendance_datetime_utc}")

                        attendance = request.env['hr.attendance'].sudo().search([
                            ('employee_id', '=', employee.id),
                            ('check_in', '>=', today_start),
                            ('check_in', '<=', today_end)
                        ], order='check_in asc', limit=1)

                        if attendance:
                            attendance.sudo().write({'check_out': attendance_datetime_utc})
                            _logger.info(f"Check Out atualizado para {employee.name} às {attendance_datetime_utc}")
                        else:
                            _logger.warning(f"Nenhum Check In encontrado para {employee.name}, ignorando Check Out.")

                        notification = request.env['attendance.notification'].sudo().search([
                            ('employee_id', '=', employee.id),
                            ('check_out', '=', False)
                        ], order='check_in desc', limit=1)

                        if notification:
                            notification.sudo().write({'check_out': attendance_datetime_utc})
                            _logger.info(
                                f"Check Out atualizado na notificação de {employee.name} às {attendance_datetime_utc}")

                            threading.Thread(target=self.send_to_relevant_websockets,
                                             args=(employee.id,
                                                   attendance_datetime_utc.strftime('%Y-%m-%d %H:%M:%S'),
                                                   employee.name,
                                                   'check-out',
                                                   notify_ids)).start()
                        else:
                            _logger.warning(f"Nenhuma notificação de Check In encontrada para {employee.name}.")

                return http.Response("OK", status=200)

            return http.Response("OK", status=200)

        except Exception as e:
            _logger.error(f"Erro inesperado ao processar os dados: {e}")
            return http.Response("Internal Server Error", status=500)

    def send_to_relevant_websockets(self, employee_id, timestamp, employee_name, action, notify_employee_ids):
        try:
            if not notify_employee_ids:
                print(f"Nenhum funcionário a notificar para {employee_name}. Nenhuma mensagem enviada.")
                return

            message_data = {
                'employee_id': employee_id,
                'attendance_datetime': timestamp,
                'status': action,
                'employee_name': employee_name,
            }

            print(f"🔹 Enviando mensagem para os WebSockets dos funcionários a notificar: {notify_employee_ids}")

            for notify_employee_id in notify_employee_ids:
                print(f"🔸 Enviando para funcionário {notify_employee_id}")
                self.send_message_to_websockets(message_data, notify_employee_id)

        except Exception as e:
            _logger.error(f"Erro ao enviar mensagem WebSocket: {e}")

    def send_message_to_websockets(self, message_data, notify_employee_id):
        uri = f"ws://localhost:8765/{notify_employee_id}"
        print(f"📤 Enviando mensagem para WebSocket: {uri} com dados: {message_data}")

        try:
            asyncio.run(self.send_message(uri, message_data))
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem via WebSocket para o funcionário {notify_employee_id}: {e}")

    async def send_message(self, uri, message_data):
        async with websockets.connect(uri) as websocket:
            await websocket.send(str(message_data))
