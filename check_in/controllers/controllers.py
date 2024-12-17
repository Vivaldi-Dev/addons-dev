# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import werkzeug
import json
from datetime import datetime, timedelta

from odoo.addons.authmodel.controllers.decorators.token_required import token_required


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

    @token_required
    @http.route('/api/monitoring/presents', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def presentes(self, **kw):
        try:
            data = request.jsonrequest
            print(data)
            if not data:
                return {'error': 'company is required'}

            company_id = data.get('company_id')
            if not company_id:
                return werkzeug.wrappers.Response(
                    json.dumps({'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            today = datetime.today().date()
            domain = [('company_id', '=', int(company_id))]
            employees = request.env['hr.employee'].sudo().search(domain)

            rcords = []
            presentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(today, datetime.min.time())),
                    ('check_in', '<', datetime.combine(today, datetime.max.time()))
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

            return rcords

        except Exception as e:
            return {'error': str(e)}

    @token_required
    @http.route('/api/monitoring/ausentes', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def ausentes(self, **kw):
        try:

            data = request.jsonrequest
            print(data)
            if not data:
                return {'error': 'company is required'}

            # Obter o campo company_id
            company_id = data.get('company_id')
            if not company_id:
                return werkzeug.wrappers.Response(
                    json.dumps({'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            today = datetime.today().date()

            domain = [('company_id', '=', int(company_id))]
            employees = request.env['hr.employee'].sudo().search(domain)

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

            return rcords

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/monitoring/percentages', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def percentages(self, **kw):
        return self.calculate_percentage(time_frame="day")

    @http.route('/api/monitoring/percentages_weekly', auth='none', cors='*', csrf=False, methods=['POST'])
    def percentages_weekly(self, **kw):
        return self.calculate_percentage(time_frame="week")

    @http.route('/api/monitoring/percentages_monthly', auth='none', cors='*', csrf=False, methods=['POST'])
    def percentages_monthly(self, **kw):
        return self.calculate_percentage(time_frame="month")

    def calculate_percentage(self, time_frame="day"):
        try:
            today = datetime.today().date()

            if time_frame == "day":
                start_date = today
                end_date = today
            elif time_frame == "week":
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            elif time_frame == "month":
                start_date = today.replace(day=1)
                end_date = (start_date.replace(month=start_date.month % 12 + 1, day=1) - timedelta(days=1))

            employees = request.env['hr.employee'].sudo().search([])

            total_employees = len(employees)
            if total_employees == 0:
                return http.Response(
                    json.dumps({'error': 'No employees found'}),
                    content_type='application/json',
                    status=400
                )

            presentes = 0
            ausentes = 0

            for employee in employees:
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(start_date, datetime.min.time())),
                    ('check_in', '<=', datetime.combine(end_date, datetime.max.time()))
                ])

                if attendance:
                    presentes += 1
                else:
                    ausentes += 1

            percentage_presentes = round((presentes / total_employees) * 100) if total_employees > 0 else 0
            percentage_ausentes = round((ausentes / total_employees) * 100) if total_employees > 0 else 0

            response_data = {
                'time_frame': time_frame,
                'total_employees': total_employees,
                'presentes': presentes,
                'ausentes': ausentes,
                'percentage_presentes': f'{percentage_presentes}%',
                'percentage_ausentes': f'{percentage_ausentes}%'
            }

            return response_data

        except Exception as e:
            # Caso haja algum erro, retornar o erro em formato JSON
            return http.Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500
            )

    @http.route('/monitoring/overview', auth='none', cors='*', csrf=False)
    def overview(self, **kw):
        table = request.env['hr.employee'].sudo().search([], limit=1)
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

            employees = request.env['hr.employee'].sudo().search([])
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

    @http.route('/monitoring/dailydelays', auth='none', cors='*', csrf=False, methods=['GET'])
    def dailydelays(self, **kw):

        records = request.env['hr.attendance'].sudo().search([('id', '=', '21')])

        info = []

        for row in records:
            check_in = row.check_in.strftime('%H:%M') if row.check_in else 'N/A'
            check_out = row.check_out.strftime('%H:%M') if row.check_out else 'N/A'

            resource_calendar_data = []
            if row.employee_id.resource_calendar_id:

                attendance_data = []
                for attendance in row.employee_id.resource_calendar_id.attendance_ids:
                    attendance_data.append({
                        'id': attendance.id,
                        'name': attendance.name,
                        'hour_from': attendance.hour_from,
                    })

                resource_calendar_data = [{
                    'id': row.employee_id.resource_calendar_id.id,
                    'name': row.employee_id.resource_calendar_id.name,
                    'attendance_ids': attendance_data
                }]
            else:
                resource_calendar_data = [{
                    'id': 'N/A',
                    'name': 'N/A',
                    'attendance_ids': []
                }]

            info.append({
                'id': row.id,
                'name': row.employee_id.name,
                'check_in': check_in,
                'check_out': check_out,
                'resource_calendar_id': resource_calendar_data
            })

        return werkzeug.wrappers.Response(
            json.dumps(info),
            headers=[('Content-Type', 'application/json')],
            status=200
        )

    @http.route('/api/monitoring/daily_delays_check', auth='none', type="json", cors='*', csrf=False, methods=['POST'])
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

        return delays_info

    @http.route('/api/company', auth='none', cors='*', csrf=False, methods=['GET'])
    def company(self):
        records = request.env['res.company'].sudo().search([])
        info = []
        for row in records:
            info.append({
                'id': row.id,
                'name': row.name,
            })
        return werkzeug.wrappers.Response(json.dumps(info), headers=[('Content-Type', 'application/json')], status=200)

    @http.route('/api/overtime', auth='none', type="json", cors='*', csrf=False, methods=['GET'])
    def overtime(self):

        employees = request.env['hr.employee'].sudo().search([])
        overtime_info = []

        for employee in employees:

            records = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '!=', False),
            ])

            if records:
                for row in records:
                    overtime_info.append({
                        'employee_name': employee.name,
                        'check_out': row.check_out.strftime('%H:%M'),

                    })

        return overtime_info

    @http.route('/api/employees_by_company', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def get_employees_by_company(self, **kw):
        try:
            data = request.jsonrequest
            company_id = data.get('company_id')

            if not company_id:
                return werkzeug.wrappers.Response(
                    json.dumps({'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            employees_count = request.env['hr.employee'].sudo().search_count([('company_id', '=', int(company_id))])

            return {'employees_count': employees_count}

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/monitoring/daily_overtime_check', auth='none', type="json", cors='*', csrf=False,
                methods=['POST'])
    def daily_overtime_check(self, **kw):
        # Obtém os dados da requisição
        data = request.jsonrequest

        if not data or 'company_id' not in data:
            return {'error': 'O campo "company_id" é obrigatório.'}

        company_id = data['company_id']

        employees = request.env['hr.employee'].sudo().search([('company_id', '=', company_id)])

        overtime_info = []
        today = datetime.today()

        for employee in employees:
            # Busca os registros de check_out no dia atual (hoje)
            records = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '>=', datetime.combine(today, datetime.min.time())),
                ('check_out', '<', datetime.combine(today, datetime.max.time()))
            ])

            for row in records:
                check_out = row.check_out
                if not check_out:
                    continue

                if check_out.date() != today.date():
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

                check_out_time = check_out.time()

                expected_time = (datetime.min + timedelta(hours=attendance.hour_to)).time()

                is_overtime = check_out_time > expected_time

                if not is_overtime:
                    continue

                overtime_str = "0 min"
                if is_overtime:
                    check_out_datetime = datetime.combine(today, check_out_time)
                    expected_datetime = datetime.combine(today, expected_time)

                    overtime_delta = check_out_datetime - expected_datetime
                    overtime_minutes = overtime_delta.total_seconds() / 60

                    if overtime_minutes >= 60:
                        overtime_hours = overtime_minutes // 60
                        remaining_minutes = overtime_minutes % 60
                        if remaining_minutes > 0:
                            overtime_str = f"{int(overtime_hours)} h {int(remaining_minutes)} min"
                        else:
                            overtime_str = f"{int(overtime_hours)} h"
                    else:
                        overtime_str = f"{int(overtime_minutes)} min"

                overtime_info.append({
                    'id': row.id,
                    'employee_name': row.employee_id.name,
                    'check_out': check_out.strftime('%H:%M'),
                    'expected_time': expected_time.strftime('%H:%M'),
                    'is_overtime': is_overtime,
                    'overtime': overtime_str
                })

        return overtime_info