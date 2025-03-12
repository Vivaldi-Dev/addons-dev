# -*- coding: utf-8 -*-
from datetime import datetime

from docutils.nodes import table

from odoo import http
from odoo.http import request
import werkzeug
import json


class CheckIn(http.Controller):

    @http.route('/monitoring/check_in', auth='none', cors='*', csrf=False)
    def check_in(self, **kw):
        try:
            employees = request.env['hr.employee'].sudo().search([])

            rcords = []
            presentes = 0
            ausentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if attendance:
                    check_in = attendance.check_in.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_in else None
                    check_out = attendance.check_out.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_out else None
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': check_in,
                        'status': 'presente'
                    })
                    presentes += 1
                else:
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': None,
                        'status': 'ausente'
                    })
                    ausentes += 1

            return werkzeug.wrappers.Response(
                json.dumps({
                    'presentes': presentes,
                    'ausentes': ausentes,
                    'dados': rcords
                }),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/presents', auth='none', cors='*', csrf=False)
    def presentes(self, **kw):
        try:
            employees = request.env['hr.employee'].sudo().search([])

            rcords = []
            presentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if attendance:
                    check_in = attendance.check_in.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_in else None
                    check_out = attendance.check_out.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_out else None
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': check_in,
                        'check_out': check_out,
                        'status': 'presente'
                    })
                    presentes += 1
            return werkzeug.wrappers.Response(
                json.dumps({
                    'total_presentes': presentes,
                    'dados': rcords
                }),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/ausentes', auth='none', cors='*', csrf=False)
    def ausentes(self, **kw):
        try:
            employees = request.env['hr.employee'].sudo().search([])

            rcords = []
            ausentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if not attendance:
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': None,
                        'check_out': None,
                        'status': 'ausente'
                    })
                    ausentes += 1

            return werkzeug.wrappers.Response(
                json.dumps({
                    'total_ausentes': ausentes,
                    'dados': rcords
                }),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/late', auth='none', cors='*', csrf=False)
    def late(self, **kw):

        employees = request.env['hr.employee'].sudo().search([])

        info = []

        for employee in employees:
            if employee.resource_calendar_id:
                resource_calendar = employee.resource_calendar_id

                calendar_details = []

                for attendance in resource_calendar.attendance_ids:
                    calendar_details.append({
                        'id': attendance.name,
                        'dayofweek': attendance.dayofweek,
                        'dayperiod': attendance.day_period,
                        'hour_from': attendance.hour_from,
                        'hour_to': attendance.hour_to

                    })

                info.append({
                    'id': employee.id,
                    'name': employee.name,
                    'resource_calendar_id': calendar_details
                })
            else:

                info.append({
                    'id': employee.id,
                    'resource_calendar_id': []
                })
        return werkzeug.wrappers.Response(
            json.dumps(info),
            headers=[('Content-Type', 'application/json')],
            status=200
        )

    @http.route('/monitoring/percentages', auth='none', cors='*', csrf=False)
    def percentages(self, **kw):
        try:
            employees = request.env['hr.employee'].sudo().search([])

            total_employees = len(employees)
            if total_employees == 0:
                return werkzeug.wrappers.Response(
                    json.dumps({
                        'error': 'No employees found'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            presentes = 0
            ausentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if attendance:
                    presentes += 1
                else:
                    ausentes += 1

            percentage_presentes = round((presentes / total_employees) * 100)
            percentage_ausentes = round((ausentes / total_employees) * 100)

            return werkzeug.wrappers.Response(
                json.dumps({
                    'total_employees': total_employees,
                    'presentes': presentes,
                    'ausentes': ausentes,
                    'percentage_presentes': f'{percentage_presentes}%',
                    'percentage_ausentes': f'{percentage_ausentes}%'
                }),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/overview', auth='none', cors='*', csrf=False)
    def overview(self, **kw):
        try:
            employees = request.env['hr.employee'].sudo().search([])
            total_employees = len(employees)
            presentes = 0
            ausentes = 0

            records = []

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if employee.resource_calendar_id:
                    resource_calendar = employee.resource_calendar_id
                    expected_entry_time = None

                    # Obter o horário esperado de entrada com base no dia da semana
                    for attendance_rule in resource_calendar.attendance_ids:
                        if int(attendance_rule.dayofweek) == datetime.today().weekday():
                            expected_entry_time = datetime.strptime(
                                f"{int(attendance_rule.hour_from):02}:00:00", '%H:%M:%S'
                            ).time()

                    if attendance:
                        check_in = attendance.check_in
                        check_in_time = check_in.time()  # Apenas a hora do check_in

                        if expected_entry_time and check_in_time > expected_entry_time:
                            late_status = 'atrasado'
                        else:
                            late_status = 'no_time'

                        records.append({
                            'id': employee.id,
                            'name': employee.name,
                            'check_in': check_in.strftime('%H:%M:%S'),  # Retorna apenas a hora
                            'status': 'presente',
                            'late_status': late_status
                        })
                        presentes += 1
                    else:
                        records.append({
                            'id': employee.id,
                            'name': employee.name,
                            'check_in': None,
                            'status': 'ausente',
                            'late_status': 'não se aplica'
                        })
                        ausentes += 1
                else:
                    # Funcionário sem calendário de trabalho
                    records.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': None,
                        'status': 'sem calendário de trabalho',
                        'late_status': 'não se aplica'
                    })

            # Calculando porcentagens
            percentage_presentes = round((presentes / total_employees) * 100) if total_employees > 0 else 0
            percentage_ausentes = round((ausentes / total_employees) * 100) if total_employees > 0 else 0

            # Retorno da resposta
            return werkzeug.wrappers.Response(
                json.dumps({
                    'total_employees': total_employees,
                    'presentes': presentes,
                    'ausentes': ausentes,
                    'percentage_presentes': f'{percentage_presentes}%',
                    'percentage_ausentes': f'{percentage_ausentes}%',
                    'dados': records
                }),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    # ------------------------------------------------------------------------------------
    @http.route('/monitoring/presents', auth='none', cors='*', csrf=False)
    def presentes(self, **kw):
        try:
            employees = request.env['hr.employee'].sudo().search([])

            rcords = []
            presentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if attendance:
                    check_in = attendance.check_in.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_in else None
                    check_out = attendance.check_out.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_out else None
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': check_in,
                        'check_out': check_out,
                        'status': 'presente'
                    })
                    presentes += 1
            return werkzeug.wrappers.Response(
                json.dumps(rcords),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/ausentes', auth='none', cors='*', csrf=False)
    def ausentes(self, **kw):
        try:
            employees = request.env['hr.employee'].sudo().search([])

            rcords = []
            ausentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if not attendance:
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': None,
                        'check_out': None,
                        'status': 'ausente'
                    })
                    ausentes += 1

            return werkzeug.wrappers.Response(
                json.dumps(rcords),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/percentages', auth='none', cors='*', csrf=False)
    def percentages(self, **kw):

        try:
            employees = request.env['hr.employee'].sudo().search([])

            total_employees = len(employees)
            if total_employees == 0:
                return werkzeug.wrappers.Response(
                    json.dumps({
                        'error': 'No employees found'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            presentes = 0
            ausentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if attendance:
                    presentes += 1
                else:
                    ausentes += 1

            percentage_presentes = round((presentes / total_employees) * 100)
            percentage_ausentes = round((ausentes / total_employees) * 100)

            return werkzeug.wrappers.Response(
                json.dumps({
                    'total_employees': total_employees,
                    'presentes': presentes,
                    'ausentes': ausentes,
                    'percentage_presentes': f'{percentage_presentes}%',
                    'percentage_ausentes': f'{percentage_ausentes}%'
                }),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
# tudo
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import werkzeug
import json
from datetime import datetime


class CheckIn(http.Controller):

    @http.route('/monitoring/check_in', auth='none', cors='*', csrf=False)
    def check_in(self, **kw):
        try:
            employees = request.env['hr.employee'].sudo().search([])

            rcords = []
            presentes = 0
            ausentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if attendance:
                    check_in = attendance.check_in.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_in else None
                    check_out = attendance.check_out.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_out else None
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': check_in,
                        'status': 'presente'
                    })
                    presentes += 1
                else:
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': None,
                        'status': 'ausente'
                    })
                    ausentes += 1

            return werkzeug.wrappers.Response(
                json.dumps({
                    'presentes': presentes,
                    'ausentes': ausentes,
                    'dados': rcords
                }),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/presents', auth='none', cors='*', csrf=False)
    def presentes(self, **kw):
        try:
            # Obter a data atual sem a parte de hora, minuto e segundo
            today = datetime.today().date()

            # Buscar os empregados
            employees = request.env['hr.employee'].sudo().search([])

            rcords = []
            presentes = 0

            for employee in employees:
                # Buscar apenas as presenças do dia atual
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(today, datetime.min.time())),
                    ('check_in', '<', datetime.combine(today, datetime.max.time()))
                ], limit=1)

                if attendance:
                    # Converter para string no formato desejado
                    check_in = attendance.check_in.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_in else None
                    check_out = attendance.check_out.strftime('%Y-%m-%dT%H:%M:%S') if attendance.check_out else None
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': check_in,
                        'check_out': check_out,
                        'status': 'presente'
                    })
                    presentes += 1

            return werkzeug.wrappers.Response(
                json.dumps(rcords),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/ausentes', auth='none', cors='*', csrf=False)
    def ausentes(self, **kw):
        try:

            today = datetime.today().date()

            employees = request.env['hr.employee'].sudo().search([])

            rcords = []
            ausentes = 0

            for employee in employees:

                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(today, datetime.min.time())),
                    ('check_in', '<', datetime.combine(today, datetime.max.time()))
                ], limit=1)

                if not attendance:
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': None,
                        'check_out': None,
                        'status': 'ausente'
                    })
                    ausentes += 1

            return werkzeug.wrappers.Response(
                json.dumps(rcords),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/percentages', auth='none', cors='*', csrf=False)
    def percentages(self, **kw):
        try:
            today = datetime.today().date()

            employees = request.env['hr.employee'].sudo().search([])

            total_employees = len(employees)
            if total_employees == 0:
                return werkzeug.wrappers.Response(
                    json.dumps({
                        'error': 'No employees found'
                    }),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            presentes = 0
            ausentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(today, datetime.min.time())),
                    ('check_in', '<', datetime.combine(today, datetime.max.time()))
                ], limit=1)

                if attendance:
                    presentes += 1
                else:
                    ausentes += 1

            percentage_presentes = round((presentes / total_employees) * 100) if total_employees > 0 else 0
            percentage_ausentes = round((ausentes / total_employees) * 100) if total_employees > 0 else 0

            return werkzeug.wrappers.Response(
                json.dumps({
                    'total_employees': total_employees,
                    'presentes': presentes,
                    'ausentes': ausentes,
                    'percentage_presentes': f'{percentage_presentes}%',
                    'percentage_ausentes': f'{percentage_ausentes}%'
                }),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/monitoring/overview', auth='none', cors='*', csrf=False)
    def overview(self, **kw):
        table = request.env['hr.employee'].sudo().search([('id', '=', '22')], limit=1)
        info = []

        for employee in table:
            employee_info = {
                'id': employee.id,
                'name': employee.name,
                'attendance_ids': [],
                'resource_calendar_id': [],
            }

            for attendance in employee.attendance_ids:
                employee_info['attendance_ids'].append({
                    'check_in': attendance.check_in.strftime('%H:%M') if attendance.check_in else '',
                })

            if employee.resource_calendar_id:
                resource_calendar = employee.resource_calendar_id
                for attendance in resource_calendar.attendance_ids:
                    hours, minutes = divmod(int(attendance.hour_from * 60), 60)
                    formatted_hour = f"{hours:02}:{minutes:02}"

                    employee_info['resource_calendar_id'].append({
                        'id': attendance.id,
                        'name': attendance.name,
                        'hour_from': formatted_hour,
                    })

            info.append(employee_info)

        return werkzeug.wrappers.Response(json.dumps(info), headers=[('Content-Type', 'application/json')], status=200)

    @http.route('/monitoring/check_attendance', auth='none', cors='*', csrf=False)
    def check_attendance(self, **kw):
        employees = request.env['hr.employee'].sudo().search([])

        late_employees = []

        days_of_week = {
            0: "Segunda-feira",
            1: "Terça-feira",
            2: "Quarta-feira",
            3: "Quinta-feira",
            4: "Sexta-feira",
            5: "Sábado",
            6: "Domingo"
        }

        for employee in employees:

            first_check_in = None
            first_scheduled_time = None

            attendance_info = []

            for attendance in employee.attendance_ids:
                check_in_time = attendance.check_in

                if not check_in_time:
                    continue

                day_of_week = check_in_time.weekday()

                if first_check_in is None or check_in_time < first_check_in:
                    first_check_in = check_in_time

                    if day_of_week == 6:
                        first_scheduled_time = "09:00"
                    else:
                        first_scheduled_time = "08:00"

            if first_check_in and first_scheduled_time:
                check_in_minutes = int(first_check_in.hour * 60 + first_check_in.minute)
                scheduled_minutes = int(first_scheduled_time.split(":")[0]) * 60 + int(
                    first_scheduled_time.split(":")[1])

                is_late = check_in_minutes > scheduled_minutes

                day_name = days_of_week.get(day_of_week, "Desconhecido")

                attendance_info.append({
                    'check_in': first_check_in.strftime('%H:%M'),
                    'scheduled_time': first_scheduled_time,
                    'is_late': is_late,
                    'day_of_week': day_name
                })

                late_employees.append({
                    'employee_id': employee.id,
                    'name': employee.name,
                    'attendance_info': attendance_info,
                })

        return werkzeug.wrappers.Response(
            json.dumps(late_employees),
            headers=[('Content-Type', 'application/json')],
            status=200
        )

    @http.route('/monitoring/ausentesday', auth='none', cors='*', csrf=False)
    def ausentesdays(self, **kw):
        try:

            employees = request.env['hr.employee'].sudo().search([('id', '=', '20')])
            now = datetime.now()
            rcords = []
            ausentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if not attendance:
                    rcords.append({
                        'id': employee.id,
                        'name': employee.name,
                        'check_in': None,
                        'check_out': None,
                        'status': 'ausente'
                    })
                    ausentes += 1

                    delta = now - now
                    number_of_days = 1.0

                    print(delta)
                    print(number_of_days)

                request.env['hr.leave'].sudo().create({
                    'holiday_status_id': 7,
                    'employee_id': employee.id,
                    'date_from': now,
                    'date_to': now,
                    'request_date_from': now,
                    'request_date_to': now,
                    'number_of_days': number_of_days,
                    'duration_display': number_of_days
                })

            return werkzeug.wrappers.Response(
                json.dumps(rcords),
                headers=[('Content-Type', 'application/json')],
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
