# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request
import json

import logging
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from datetime import datetime


class ZKTecoController(http.Controller):
    @http.route('/iclock/cdata', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def receive_records(self, **kwargs):
        if request.httprequest.method == 'POST':
            post_content = request.httprequest.data.decode('utf-8')

            # Obtener el número de serie (SN) de los parámetros de la URL
            sn = kwargs.get('SN')
            if not sn:
                _logger = logging.getLogger(__name__)
                _logger.error("Número de serie (SN) no encontrado en la solicitud.")
                return "Error: Número de serie no encontrado"

            # Opcional: Imprimir el contenido recibido para depuración
            _logger = logging.getLogger(__name__)
            _logger.info("Datos recibidos de ZKTeco: %s", post_content)

            # Buscar la máquina usando el número de serie (SN)
            machine = request.env['zk.machine'].sudo().search([('name', '=', sn)], limit=1)
            if not machine:
                raise UserError(f'Máquina con SN {sn} no encontrada.')

            # Obtener el área de trabajo (res.partner) asociado con la máquina
            work_area = machine.address_id

            # Procesar los datos del POST (ejemplo: "1010 2024-12-04 12:36:23 0 4 0 0 0 0 0 0")
            data_lines = post_content.splitlines()

            for line in data_lines:
                # Dividir los campos (suponiendo que los campos están separados por tabuladores)
                fields = line.split('\t')

                # Asignar los valores de los campos a las variables correspondientes
                if len(fields) < 10:
                    _logger.warning(f"Datos incompletos en la línea: {line}")
                    continue  # Si los datos no tienen los campos esperados, ignoramos esta línea.

                device_id = fields[0]  # El primer campo es el device_id
                timestamp = fields[1]  # El segundo campo es la fecha y hora de la marcación
                punch_type = fields[2]  # El tercer campo es el tipo de marcación (Check In/Check Out, etc.)
                attendance_type = fields[3]  # El cuarto campo es el tipo de asistencia (Huella, rostro, etc.)

                # Buscar al empleado basado en el device_id (ID del dispositivo biométrico)
                employee = request.env['hr.employee'].sudo().search([('device_id', '=', device_id)], limit=1)
                if not employee:
                    _logger.warning(f"Empleado no encontrado para el device_id: {device_id}")
                    continue

                # Convertir la fecha y hora de la marcación al formato adecuado
                try:
                    attendance_datetime = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    _logger.warning(f"Fecha y hora inválida en la línea: {line}")
                    continue

                    # Procesar Check In o Check Out
                if punch_type == '0':  # Check In
                    # Crear un registro de entrada
                    request.env['hr.attendance'].sudo().create({
                        'employee_id': employee.id,
                        'check_in': attendance_datetime,
                        'punching_time': attendance_datetime,
                        'punch_type': punch_type,
                        'attendance_type': attendance_type,
                        'address_id': work_area.id,
                    })
                    _logger.info("Registrado Check In para empleado %s en %s", employee.name, attendance_datetime)

                elif punch_type == '1':  # Check Out
                    # Buscar el último Check In sin Check Out
                    attendance = request.env['hr.attendance'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('check_out', '=', False)
                    ], order='check_in desc', limit=1)

                    if attendance:
                        # Actualizar el registro con la hora de salida
                        attendance.sudo().write({'check_out': attendance_datetime})
                        _logger.info("Registrado Check Out para empleado %s en %s", employee.name, attendance_datetime)
                    else:
                        _logger.warning("No se encontró un Check In previo para el empleado %s.", employee.name)
                else:
                    _logger.warning("Tipo de marcación no soportado: %s", punch_type)

        return http.Response("OK", status=200)
