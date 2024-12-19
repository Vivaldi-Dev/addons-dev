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

                    threading.Thread(target=self.send_to_relevant_websockets, args=(employee.id, attendance_datetime)).start()

                elif punch_type == '1':
                    attendance = request.env['hr.attendance'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('check_out', '=', False)
                    ], order='check_in desc', limit=1)

                    if attendance:
                        attendance.sudo().write({'check_out': attendance_datetime})
                        _logger.info("Registrado Check Out para empleado %s en %s", employee.name, attendance_datetime)
                    else:
                        _logger.warning("No se encontró un Check In previo para el empleado %s.", employee.name)
                else:
                    _logger.warning("Tipo de marcación no soportado: %s", punch_type)

        return http.Response("OK", status=200)

    import asyncio
    import websockets
    from datetime import datetime

    class ZKTecoController(http.Controller):

        @http.route('/api/monitoring/daily_delays_check', auth='none', type="json", cors='*', csrf=False,
                    methods=['POST'])
        def daily_delays_check(self, **kw):

            data = request.jsonrequest

            if not data:
                return {'error': 'O campo "company_id" é obrigatório.'}

            company_id = data.get('company_id')

            employees = request.env['hr.employee'].sudo().search([('company_id', '=', company_id)])

            delays_info = []
            today = datetime.today()

            for employee in employees:
                records = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(today, datetime.min.time())),
                    ('check_in', '<', datetime.combine(today, datetime.max.time()))
                ])

                for row in records:
                    check_in = row.check_in
                    if not check_in:
                        continue

                    if check_in.date() != today.date():
                        continue

                    resource_calendar = row.employee_id.resource_calendar_id
                    if not resource_calendar:
                        continue

                    attendance = next(
                        (att for att in resource_calendar.attendance_ids if int(att.dayofweek) == today.weekday()),
                        None
                    )

                    if not attendance:
                        continue

                    check_in_time = check_in.time()
                    expected_time = (datetime.min + timedelta(hours=attendance.hour_from)).time()

                    is_late = check_in_time > expected_time

                    if not is_late:
                        continue

                    delay_str = "0 min"
                    if is_late:
                        check_in_datetime = datetime.combine(today, check_in_time)
                        expected_datetime = datetime.combine(today, expected_time)

                        delay_delta = check_in_datetime - expected_datetime
                        delay_minutes = delay_delta.total_seconds() / 60

                        if delay_minutes >= 60:
                            delay_hours = delay_minutes // 60
                            remaining_minutes = delay_minutes % 60
                            if remaining_minutes > 0:
                                delay_str = f"{int(delay_hours)} h {int(remaining_minutes)} min"
                            else:
                                delay_str = f"{int(delay_hours)} h"
                        else:
                            delay_str = f"{int(delay_minutes)} min"

                    delays_info.append({
                        'id': row.id,
                        'employee_name': row.employee_id.name,
                        'check_in': check_in.strftime('%H:%M'),
                        'expected_time': expected_time.strftime('%H:%M'),
                        'is_late': is_late,
                        'delay': delay_str
                    })

                    # Enviar dados de atrasos via WebSocket para cada funcionário atrasado
                    if is_late:
                        self.send_delay_notification(employee.id, delay_str, check_in.strftime('%H:%M'))

            return delays_info


    def send_to_relevant_websockets(self, employee_id, attendance_datetime):

        formatted_datetime = attendance_datetime.strftime('%Y-%m-%d %H:%M:%S')

        message_data = {
            'employee_id': employee_id,
            'attendance_datetime': formatted_datetime,
            'status': 'Check In' if attendance_datetime else 'Check Out'
        }

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
