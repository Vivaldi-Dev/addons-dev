# -*- coding: utf-8 -*-
from calendar import monthrange
from datetime import datetime, timedelta

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

    @http.route('/api/report/overtime', type='json', auth='none', cors='*', csrf=False, methods=['POST'])
    def overtime(self, **kw):
        try:
            data = request.jsonrequest
            company_id = data.get('company_id')
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')

            if not company_id or not start_date_str or not end_date_str:
                return {'error': 'Company ID, start_date, and end_date are required'}

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                return {'error': 'Invalid date format. Use YYYY-MM-DD'}

            if start_date > end_date:
                return {'error': 'start_date cannot be greater than end_date'}

            current_year = datetime.now().year
            current_month = datetime.now().month

            if start_date.year == current_year and end_date.year == current_year:
                if end_date.month > current_month:
                    return {'error': 'You cannot request a report for future months in the current year'}

            employees = request.env['hr.employee'].sudo().search([('company_id', '=', company_id)])
            total_employees = len(employees)

            attendances = request.env['hr.attendance'].sudo().search([
                ('employee_id', 'in', employees.ids),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date + timedelta(days=1))
            ])

            daily_report = []
            global_present_count = 0
            global_absent_count = 0
            current_date = start_date

            while current_date <= end_date:
                day_start = datetime.combine(current_date, datetime.min.time())
                day_end = datetime.combine(current_date, datetime.max.time())
                daily_attendances = attendances.filtered(
                    lambda a: day_start <= a.check_in <= day_end
                )

                present_ids = daily_attendances.mapped('employee_id.id')
                absent_ids = list(set(employees.ids) - set(present_ids))

                present_count = len(present_ids)
                absent_count = len(absent_ids)

                global_present_count += present_count
                global_absent_count += absent_count

                daily_report.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'day_of_week': current_date.strftime('%A'),
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'present_employees': [
                        {'id': emp.id, 'name': emp.name} for emp in employees if emp.id in present_ids
                    ],
                    'absent_employees': [
                        {'id': emp.id, 'name': emp.name} for emp in employees if emp.id in absent_ids
                    ]
                })

                current_date += timedelta(days=1)

            report_data = {
                'company_id': company_id,
                'date_range': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                },
                'total_employees': total_employees,
                'global_summary': {
                    'total_present': global_present_count,
                    'total_absent': global_absent_count
                },
                'daily_report': daily_report
            }

            return report_data

        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/monitoring/employee/checkin_summary', type='json', auth='none', cors='*', csrf=False,
                methods=['POST'])
    def employee_checkin_summary(self, **kw):

        data = request.jsonrequest
        employee_id = data.get('employee_id')
        month = data.get('month')

        if not employee_id or not month:
            return {"error": "Os campos 'employee_id', 'month' e 'year' são obrigatórios."}

        try:
            month = int(month)

        except ValueError:
            return {"error": "Os campos 'month' e 'year' devem ser inteiros válidos."}

        if not 1 <= month <= 12:
            return {"error": "O campo 'month' deve estar entre 1 e 12."}

        try:
            employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)
            if not employee:
                return {"error": "Employee not found"}

            year = datetime.now().year

            num_days = monthrange(year, month)[1]
            all_days = [
                datetime(year, month, day).date()
                for day in range(1, num_days + 1)
                if datetime(year, month, day).weekday() != 6
            ]

            attendance_records = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', datetime(year, month, 1)),
                ('check_in', '<', datetime(year, month, num_days) + timedelta(days=1))
            ])
            check_in_days = {record.check_in.date() for record in attendance_records if record.check_in}

            days_with_checkin = [day.isoformat() for day in all_days if day in check_in_days]
            days_without_checkin = [day.isoformat() for day in all_days if day not in check_in_days]

            summary = {
                'employee_id': employee.id,
                'employee_name': employee.name,
                'total_business_days': len(all_days),
                'days_with_checkin': len(days_with_checkin),
                'days_without_checkin': len(days_without_checkin),
            }

            return summary

        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}

    @token_required
    @http.route('/api/monitoring/ausentes', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def ausentes(self, **kw):
        """
        Processes and retrieves information about absent employees with pagination.
        """
        try:
            data = request.jsonrequest

            if not data:
                return {'error': 'A requisição precisa conter dados.'}

            company_id = data.get('company_id')
            if not company_id:
                return werkzeug.wrappers.Response(
                    json.dumps({'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            start_date = data.get('start_date')
            end_date = data.get('end_date')

            tz_maputo = pytz.timezone('Africa/Maputo')
            tz_utc = pytz.utc

            if start_date:
                try:
                    start_date = tz_maputo.localize(datetime.strptime(start_date, '%Y-%m-%d')).astimezone(tz_utc)
                except ValueError:
                    return {'error': 'O campo "start_date" deve estar no formato "YYYY-MM-DD".'}
            if end_date:
                try:
                    end_date = tz_maputo.localize(datetime.strptime(end_date, '%Y-%m-%d')).astimezone(
                        tz_utc) + timedelta(days=1, seconds=-1)
                except ValueError:
                    return {'error': 'O campo "end_date" deve estar no formato "YYYY-MM-DD".'}

            if start_date and end_date and start_date > end_date:
                return {'error': 'A data inicial não pode ser posterior à data final.'}

            employees = request.env['hr.employee'].sudo().search([('company_id', '=', int(company_id))])
            total_employees = len(employees)

            records = []
            ausentes = 0

            page = int(data.get('page', 1))
            limit = int(data.get('limit', 10))
            offset = (page - 1) * limit

            for employee in employees:
                attendances = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', start_date) if start_date else (),
                    ('check_in', '<', end_date) if end_date else ()
                ])

                if not attendances:
                    records.append({
                        'id': employee.id,
                        'name': employee.name,
                        'job_position': employee.job_title,
                        'check_in': "",
                        'check_out': "",
                        'status': 'ausente'
                    })
                    ausentes += 1

            paginated_records = records[offset:offset + limit]

            return {
                'total_employees': total_employees,
                'total_ausentes': ausentes,
                'current_page': page,
                'total_pages': (len(records) + limit - 1) // limit,
                'records': paginated_records
            }

        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/monitoring/absentens', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    @coach_required
    def absentens(self, **kw):
        data = request.jsonrequest

        if not data:
            return {'error': 'A requisição precisa conter dados.'}

        company_id = data.get('company_id')
        if not company_id:
            return {'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}

        start_date = data.get('start_date')
        end_date = data.get('end_date')
        by_name = data.get('by_name')

        page = int(data.get('page', 1))
        limit = int(data.get('limit', 5))
        offset = (page - 1) * limit

        tz_maputo = pytz.timezone('Africa/Maputo')
        tz_utc = pytz.utc

        try:
            if start_date:
                start_date = tz_maputo.localize(datetime.strptime(start_date, '%Y-%m-%d')).astimezone(tz_utc)
            if end_date:
                end_date = tz_maputo.localize(datetime.strptime(end_date, '%Y-%m-%d')).astimezone(tz_utc) + timedelta(
                    days=1, seconds=-1)
        except ValueError:
            return {'error': 'As datas devem estar no formato "YYYY-MM-DD".'}

        if start_date and end_date and start_date > end_date:
            return {'error': 'A data inicial não pode ser posterior à data final.'}

        Leave = request.env['hr.leave'].sudo()

        # Filtra apenas os funcionários gerenciados pelo coach
        coached_employee_ids = kw.get('coached_employee_ids', [])
        domain = [
            ('state', 'in', ['confirm', 'refuse', 'validate']),
            ('employee_id.company_id', '=', int(company_id)),
            ('employee_id', 'in', coached_employee_ids)  # Filtra apenas os funcionários do coach
        ]

        if by_name:
            domain.append(('employee_id.name', 'ilike', by_name))

        if start_date:
            domain.append(('date_from', '>=', start_date))
        if end_date:
            domain.append(('date_to', '<=', end_date))

        state_mapping = {
            'draft': 'To Submit',
            'confirm': 'To Approve',
            'refuse': 'Refused',
            'validate1': 'Second Approval',
            'validate': 'Approved'
        }

        # Busca as ausências com paginação
        leaves = Leave.search(domain, offset=offset, limit=limit)
        total_leaves = Leave.search_count(domain)

        result = []
        for leave in leaves:
            result.append({
                'employee_id': leave.employee_id.id,
                'employee_name': leave.employee_id.name,
                'date_from': leave.date_from.strftime('%Y-%m-%d %H:%M:%S'),
                'date_to': leave.date_to.strftime('%Y-%m-%d %H:%M:%S'),
                'leave_type': leave.holiday_status_id.name,
                'state': state_mapping.get(leave.state, leave.state),
            })

        return {
            'absent_employees': result,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_records': total_leaves,
                'total_pages': (total_leaves + limit - 1) // limit
            }
        }

    @token_required
    @http.route('/api/monitoring/absentens', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    @coach_required
    def absentens(self, **kw):
        data = request.jsonrequest

        if not data:
            return {'error': 'A requisição precisa conter dados.'}

        company_id = data.get('company_id')
        if not company_id:
            return werkzeug.wrappers.Response(
                json.dumps({'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        start_date = data.get('start_date')
        end_date = data.get('end_date')
        by_name = data.get('by_name')

        page = int(data.get('page', 1))
        limit = int(data.get('limit', 5))
        offset = (page - 1) * limit

        tz_maputo = pytz.timezone('Africa/Maputo')
        tz_utc = pytz.utc

        try:
            if start_date:
                start_date = tz_maputo.localize(datetime.strptime(start_date, '%Y-%m-%d')).astimezone(tz_utc)
            if end_date:
                end_date = tz_maputo.localize(datetime.strptime(end_date, '%Y-%m-%d')).astimezone(
                    tz_utc) + timedelta(days=1, seconds=-1)
        except ValueError:
            return {'error': 'As datas devem estar no formato "YYYY-MM-DD".'}

        if start_date and end_date and start_date > end_date:
            return {'error': 'A data inicial não pode ser posterior à data final.'}

        Leave = request.env['hr.leave'].sudo()

        domain = [
            ('state', 'in', ['confirm', 'refuse', 'validate']),
            ('employee_id.company_id', '=', int(company_id)),
            ('employee_id', 'in', kw.get('coached_employee_ids', []))
        ]

        if by_name:
            domain.append(('employee_id.name', 'ilike', by_name))

        if start_date:
            domain.append(('date_from', '>=', start_date))
        if end_date:
            domain.append(('date_to', '<=', end_date))

        state_mapping = {
            'draft': 'To Submit',
            'confirm': 'To Approve',
            'refuse': 'Refused',
            'validate1': 'Second Approval',
            'validate': 'Approved'
        }

        leaves = Leave.search(domain, offset=offset, limit=limit)
        total_leaves = Leave.search_count(domain)

        result = []
        for leave in leaves:
            employee = leave.employee_id
            resource_calendar = employee.resource_calendar_id

            date_from = leave.date_from
            date_to = leave.date_to

            day_of_week = date_from.weekday()

            is_work_day = False
            for attendance in resource_calendar.attendance_ids:
                if attendance.dayofweek == str(day_of_week):
                    is_work_day = True
                    break

            if is_work_day:
                result.append({
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'description': leave.name,
                    'date_from': date_from.strftime('%Y-%m-%d %H:%M:%S'),
                    'date_to': date_to.strftime('%Y-%m-%d %H:%M:%S'),
                    'leave_type': leave.holiday_status_id.name,
                    'state': state_mapping.get(leave.state, leave.state),
                    'is_absence': True
                })
            else:
                result.append({
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'description': leave.name,
                    'date_from': date_from.strftime('%Y-%m-%d %H:%M:%S'),
                    'date_to': date_to.strftime('%Y-%m-%d %H:%M:%S'),
                    'leave_type': leave.holiday_status_id.name,
                    'state': state_mapping.get(leave.state, leave.state),
                    'is_absence': False
                })

        return {
            'absent_employees': result,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_records': total_leaves,
                'total_pages': (total_leaves + limit - 1) // limit
            }
        }

    @http.route('/api/monitoring/absentens', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def absentens(self, **kw):
        data = request.jsonrequest

        if not data:
            return {'error': 'A requisição precisa conter dados.'}

        company_id = data.get('company_id')
        if not company_id:
            return werkzeug.wrappers.Response(
                json.dumps({'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        start_date = data.get('start_date')
        end_date = data.get('end_date')
        by_name = data.get('by_name')  # Filtro opcional por nome

        # Parâmetros de paginação
        page = int(data.get('page', 1))  # Página atual (padrão: 1)
        limit = int(data.get('limit', 5))  # Número de registros por página (padrão: 5)
        offset = (page - 1) * limit  # Calcula o offset com base na página e no limite

        tz_maputo = pytz.timezone('Africa/Maputo')
        tz_utc = pytz.utc

        try:
            if start_date:
                start_date = tz_maputo.localize(datetime.strptime(start_date, '%Y-%m-%d')).astimezone(tz_utc)
            if end_date:
                end_date = tz_maputo.localize(datetime.strptime(end_date, '%Y-%m-%d')).astimezone(
                    tz_utc) + timedelta(days=1, seconds=-1)
        except ValueError:
            return {'error': 'As datas devem estar no formato "YYYY-MM-DD".'}

        if start_date and end_date and start_date > end_date:
            return {'error': 'A data inicial não pode ser posterior à data final.'}

        Leave = request.env['hr.leave'].sudo()
        domain = [
            ('state', 'in', ['confirm', 'refuse', 'validate']),
            ('employee_id.company_id', '=', int(company_id))  # Filtra diretamente pelo company_id
        ]

        # Adiciona o filtro por nome, se fornecido
        if by_name:
            domain.append(('employee_id.name', 'ilike', by_name))  # Filtra por nome (case-insensitive)

        if start_date:
            domain.append(('date_from', '>=', start_date))
        if end_date:
            domain.append(('date_to', '<=', end_date))

        state_mapping = {
            'draft': 'To Submit',
            'confirm': 'To Approve',
            'refuse': 'Refused',
            'validate1': 'Second Approval',
            'validate': 'Approved'
        }

        # Aplica a paginação
        leaves = Leave.search(domain, offset=offset, limit=limit)
        total_leaves = Leave.search_count(domain)  # Conta o total de registros sem paginação

        result = []
        for leave in leaves:
            result.append({
                'employee_id': leave.employee_id.id,
                'employee_name': leave.employee_id.name,
                'date_from': leave.date_from.strftime('%Y-%m-%d %H:%M:%S'),
                'date_to': leave.date_to.strftime('%Y-%m-%d %H:%M:%S'),
                'leave_type': leave.holiday_status_id.name,
                'state': state_mapping.get(leave.state, leave.state)
            })

        return {
            'absent_employees': result,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_records': total_leaves,
                'total_pages': (total_leaves + limit - 1) // limit  # Calcula o número total de páginas
            }
        }