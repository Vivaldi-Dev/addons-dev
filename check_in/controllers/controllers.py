import base64

from odoo import http
from odoo.http import Response
from calendar import monthrange
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
        """
        Handles the processing and querying of employee attendance information within a given company and date range.

        Provides API functionality to retrieve attendance records for employees of a specific company based on the provided
        `company_id`. If the date range `start_date` and/or `end_date` is not specified, defaults to include all attendance
        records for the current day. Validates the input and computes the total number of employees and those present, returning
        detailed attendance records in JSON format.

        @param self: Instance of the class.
        @param kw: Dictionary containing the request parameters passed in the POST request.

        @parameters:
            company_id: str
                A required parameter representing the ID of the company whose employee attendance needs to be queried.
                Must be included in the request data.
            start_date: Optional[str]
                The start of the date range to filter employee attendance.
                If provided, it must be in the format "YYYY-MM-DD".
                Defaults to the start of the current day if not specified.
            end_date: Optional[str]
                The end of the date range to filter employee attendance.
                If provided, it must be in the format "YYYY-MM-DD".
                Defaults to the end of the current day if not specified.

        @raises:
            KeyError:
                Raised if `company_id` is missing from the request data.
            ValueError:
                Raised if `start_date` or `end_date` cannot be parsed in the expected date format.
            Exception:
                Catch-all for any unexpected errors encountered during processing.

        @returns:
            dict
                JSON response detailing attendance information.
                Includes the total number of employees, total presentes (those marked as present within the date range),
                and a list of detailed attendance records. An error message is returned if processing fails.
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

            today = datetime.today()

            if start_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                except ValueError:
                    return {
                        'error': 'O campo "start_date" deve estar no formato "YYYY-MM-DD" (ex.: "2025-01-01").'}
            else:
                start_date = datetime.combine(today, datetime.min.time())

            if end_date:
                try:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1, seconds=-1)
                except ValueError:
                    return {
                        'error': 'O campo "end_date" deve estar no formato "YYYY-MM-DD" (ex.: "2025-01-05").'}
            else:
                end_date = datetime.combine(today, datetime.max.time())

            if start_date > end_date:
                return {'error': 'A data inicial não pode ser posterior à data final.'}

            employees = request.env['hr.employee'].sudo().search([('company_id', '=', int(company_id))])
            total_employees = len(employees)

            records = []
            presentes = 0

            for employee in employees:

                attendances = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', start_date),
                    ('check_in', '<=', end_date)
                ], order='check_in desc')

                for attendance in attendances:
                    check_in = attendance.check_in.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_in else None
                    check_out = attendance.check_out.strftime('%Y-%m-%d %H:%M:%S') if attendance.check_out else None
                    records.append({
                        'id': employee.id,
                        'job_position': employee.job_title,
                        'name': employee.name,
                        'check_in': check_in,
                        'check_out': check_out,
                        'status': 'presente'
                    })
                    presentes += 1

            records = sorted(records, key=lambda x: x['check_in'], reverse=True)

            return {
                'total_employees': total_employees,
                'total_presentes': presentes,
                'records': records
            }

        except Exception as e:
            return {'error': str(e)}

    @token_required
    @http.route('/api/monitoring/ausentes', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def ausentes(self, **kw):
        """
        Processes and retrieves information about absent employees within a given company, based on attendance records and optional date filters.

        Parameters:
            **kw: dict
                Additional keyword arguments from the HTTP request, which are expected to include the following:
                  - company_id (int): Mandatory. The identifier of the company to filter employees.
                  - start_date (str, optional): Start date for filtering attendance records in the format 'YYYY-MM-DD'.
                  - end_date (str, optional): End date for filtering attendance records in the format 'YYYY-MM-DD'.

        Returns:
            dict: A dictionary containing a summary of absent employees, which includes:
                  - total_employees (int): Total number of employees within the specified company.
                  - total_ausentes (int): Number of employees marked as absent based on attendance data.
                  - records (list): A list of dictionaries, each representing an absent employee, with the following details:
                     - id (int): Employee ID.
                     - name (str): Employee's name.
                     - job_position (str): Job title of the employee.
                     - check_in (None): No check-in record since it denotes absence.
                     - check_out (None): No check-out record since it denotes absence.
                     - status (str): Set to 'ausente'.

        Raises:
            KeyError: If the mandatory 'company_id' field is missing in the JSON request body.
            ValueError: If 'start_date' or 'end_date' is not in the expected 'YYYY-MM-DD' format.

        Notes:
            The function validates the presence and format of the `company_id`, `start_date`, and `end_date` fields in the
            incoming request. If both `start_date` and `end_date` are provided, their chronological order is also validated.
            Employees with no attendance records during the specified period are considered absent.
        """
        try:
            data = request.jsonrequest

            if not data:
                return {'error': 'company is required'}

            company_id = data.get('company_id')
            if not company_id:
                return werkzeug.wrappers.Response(
                    json.dumps({'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            start_date = data.get('start_date')
            end_date = data.get('end_date')

            if start_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                except ValueError:
                    return {
                        'error': 'O campo "start_date" deve estar no formato "YYYY-MM-DD" (ex.: "2025-01-01").'}
            if end_date:
                try:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1, seconds=-1)
                except ValueError:
                    return {
                        'error': 'O campo "end_date" deve estar no formato "YYYY-MM-DD" (ex.: "2025-01-05").'}

            if start_date and end_date and start_date > end_date:
                return {'error': 'A data inicial não pode ser posterior à data final.'}

            employees = request.env['hr.employee'].sudo().search([('company_id', '=', int(company_id))])
            total_employees = len(employees)

            records = []
            ausentes = 0

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
                        'check_in': None,
                        'check_out': None,
                        'status': 'ausente'
                    })
                    ausentes += 1

            return {
                'total_employees': total_employees,
                'total_ausentes': ausentes,
                'records': records
            }

        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/monitoring/percentages', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def percentages(self, **kw):
        try:
            data = request.jsonrequest
            date_from = data.get('date_from')
            date_to = data.get('date_to')
            company_id = data.get('company_id')

            if not date_from or not date_to or not company_id:
                return {'error': "'date_from', 'date_to' e 'company_id' são obrigatórios"}

            try:
                start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            except ValueError:
                return {'error': "Formato de data inválido. Use 'YYYY-MM-DD'"}

            employees = request.env['hr.employee'].sudo().search([('company_id', '=', int(company_id))])

            total_employees = len(employees)
            if total_employees == 0:
                return http.Response(
                    json.dumps({'error': 'Nenhum funcionário encontrado para a companhia fornecida'}),
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
                'date_from': date_from,
                'date_to': date_to,
                'company_id': company_id,
                'total_employees': total_employees,
                'presentes': presentes,
                'ausentes': ausentes,
                'percentage_presentes': f'{percentage_presentes}%',
                'percentage_ausentes': f'{percentage_ausentes}%'
            }

            return response_data

        except Exception as e:
            return {'error': str(e)}

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

                # Adicionando a tolerância de 10 minutos
                tolerance_time = timedelta(minutes=10)
                expected_time_with_tolerance = datetime.combine(today, expected_time) + tolerance_time
                expected_time_with_tolerance = expected_time_with_tolerance.time()

                # Verificar se o funcionário está atrasado
                is_late = check_in_time > expected_time_with_tolerance

                # Se o funcionário não estiver atrasado, ignoramos
                if not is_late:
                    continue

                delay_str = "0 min"
                if is_late:
                    check_in_datetime = datetime.combine(today, check_in_time)
                    expected_datetime = datetime.combine(today, expected_time_with_tolerance)

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

                # Adiciona apenas os atrasos
                delays_info.append({
                    'id': row.id,
                    'employee_name': row.employee_id.name,
                    'employee_id': row.employee_id.id,
                    'check_in': check_in.strftime('%H:%M'),
                    'expected_time': expected_time.strftime('%H:%M'),
                    'delay': delay_str
                })

        return delays_info

    @token_required
    @http.route('/company/company', auth='none', cors='*', csrf=False, methods=['GET'])
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

    @http.route('/api/monitoring/monitoring', auth='none', type="json", cors='*', csrf=False, methods=['POST'])
    def daily_overtime_check(self, **kw):
        data = request.jsonrequest

        if not data or 'company_id' not in data:
            return {'error': 'O campo "company_id" é obrigatório.'}

        company_id = data['company_id']

        employees = request.env['hr.employee'].sudo().search([('company_id', '=', company_id)])

        overtime_info = []
        today = datetime.today()

        for employee in employees:
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

                attendances_today = [
                    att for att in resource_calendar.attendance_ids
                    if int(att.dayofweek) == today.weekday()
                ]

                if not attendances_today:
                    continue

                afternoon_attendance = next(
                    (att for att in attendances_today if att.hour_from >= 12),
                    None
                )
                attendance = afternoon_attendance or attendances_today[0]

                expected_time = (datetime.min + timedelta(hours=attendance.hour_to)).time()

                check_out_time = check_out.time()

                is_overtime = check_out_time > expected_time

                overtime_str = "0 min"
                overtime_part1_str = "0 min"
                overtime_part2_str = "0 min"
                total_overtime_minutes = 0

                if is_overtime:
                    check_out_datetime = datetime.combine(today, check_out_time)
                    expected_datetime = datetime.combine(today, expected_time)

                    overtime_delta = check_out_datetime - expected_datetime
                    overtime_minutes = overtime_delta.total_seconds() / 60

                    expected_time_obj = datetime.combine(today, expected_time)
                    time_until_20 = datetime.combine(today, datetime.min.time()) + timedelta(hours=20)
                    overtime_until_20 = min(check_out_datetime, time_until_20) - expected_time_obj

                    overtime_until_20_minutes = max(overtime_until_20.total_seconds() / 60, 0)
                    overtime_part1_str = f"{int(overtime_until_20_minutes)} min" if overtime_until_20_minutes < 60 else f"{int(overtime_until_20_minutes // 60)}h"
                    total_overtime_minutes += overtime_until_20_minutes

                    if check_out_datetime > time_until_20:
                        overtime_after_20 = check_out_datetime - time_until_20
                        overtime_after_20_minutes = overtime_after_20.total_seconds() / 60
                        overtime_part2_str = f"{int(overtime_after_20_minutes)} min" if overtime_after_20_minutes < 60 else f"{int(overtime_after_20_minutes // 60)}h"
                        total_overtime_minutes += overtime_after_20_minutes

                    if total_overtime_minutes >= 60:
                        overtime_hours = total_overtime_minutes // 60
                        remaining_minutes = total_overtime_minutes % 60
                        if remaining_minutes > 0:
                            overtime_str = f"{int(overtime_hours)} h {int(remaining_minutes)} min"
                        else:
                            overtime_str = f"{int(overtime_hours)} h"
                    else:
                        overtime_str = f"{int(total_overtime_minutes)} min"

                overtime_info.append({
                    'id': row.id,
                    'employee_name': row.employee_id.name,
                    'check_out': check_out.strftime('%H:%M'),
                    'expected_time': expected_time.strftime('%H:%M'),
                    'is_overtime': is_overtime,
                    'overtime': overtime_str,
                    'overtime_until_20h': overtime_part1_str,
                    'overtime_after_20h': overtime_part2_str
                })

        return overtime_info

    @http.route('/api/all/employees', type='json', auth='none', methods=['POST'], csrf=False)
    def all_employee(self):
        company_id = request.httprequest.args.get('company_id')
        employee_id = request.httprequest.args.get('id')
        employee_name = request.httprequest.args.get('name')

        if not company_id:
            return {'error': 'O campo "company_id" é obrigatório.'}

        domain = [('company_id', '=', int(company_id))]

        if employee_id:
            domain.append(('id', '=', int(employee_id)))

        if employee_name:
            domain.append(('name', 'ilike', employee_name))

        employees = request.env['hr.employee'].sudo().search(domain)

        employees_info = [
            {
                'id': employee.id,
                'name': employee.name,
                'email': employee.user_id.login,
                'x_ativo': employee.x_ativo,
                'address_home_id': employee.address_home_id.bank_ids[
                    0].bank_id.name if employee.address_home_id.bank_ids else False,
                'address_cc_id': employee.address_home_id.bank_ids[
                    0].acc_number if employee.address_home_id.bank_ids else False,
            }
            for employee in employees
        ]

        return employees_info

    @http.route('/api/employees', type='json', auth='none', methods=['PUT'], csrf=False)
    def update_employee_notifications(self):
        data = request.jsonrequest
        employee_ids = data.get('employee_ids', [])
        x_ativo = data.get('is_active')

        if not employee_ids:
            return {'status': 'error', 'message': 'Os IDs dos funcionários devem ser uma lista de inteiros.',
                    'data': data}

        if not isinstance(x_ativo, bool):
            return {'status': 'error', 'message': 'O valor de "x_ativo" deve ser um booleano.', 'data': data}

        employees = request.env['hr.employee'].sudo().browse(employee_ids)

        non_existing_employees = [emp_id for emp_id in employee_ids if emp_id not in employees.ids]
        if non_existing_employees:
            return {'status': 'error', 'message': f'Funcionários com IDs {non_existing_employees} não encontrados.',
                    'data': data}

        employees.write({'x_ativo': x_ativo})

        return {'status': 'success', 'message': 'Notificação em tempo real atualizada com sucesso.', 'data': data}

    @http.route('/api/employees_avtive', type='json', auth='none', methods=['POST'], csrf=False)
    def employees_avtive(self):
        data = request.jsonrequest

        if not data or 'company_id' not in data:
            return {'error': 'O campo "company_id" é obrigatório.'}

        company_id = data['company_id']

        employees = request.env['hr.employee'].sudo().search([
            ('company_id', '=', company_id),
            ('x_ativo', '!=', False)
        ])

        if not employees:
            return {'status': 'error', 'message': 'Nenhum funcionário encontrado com o campo "x_ativo" ativo.'}

        employee_data = []
        for emp in employees:
            employee_data.append({
                'id': emp.id,
                'name': emp.name,
                'email': emp.work_email,
                'company_id': emp.company_id.id,
                'x_ativo': emp.x_ativo
            })

        return employee_data

    @http.route('/api/monitoring/employee', type='json', auth='none', cors='*', csrf=False, methods=['POST'])
    def employee_by_id(self, **kw):
        try:
            data = request.jsonrequest
            employee_id = data.get('employee_id')
            month = data.get('month')

            if not employee_id or not month:
                return {"error": "Employee ID and month are required"}

            current_year = datetime.now().year

            employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)

            if not employee:
                return {"error": "Employee not found"}

            next_month = month + 1 if month < 12 else 1
            next_month_year = current_year if month < 12 else current_year + 1

            attendance_records = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', datetime(current_year, month, 1)),
                ('check_in', '<', datetime(next_month_year, next_month, 1))
            ])

            attendance_info = [{
                'check_in': record.check_in.strftime('%Y-%m-%d %H:%M:%S') if record.check_in else None,
                'check_out': record.check_out.strftime('%Y-%m-%d %H:%M:%S') if record.check_out else None
            } for record in attendance_records]

            employee_info = {
                'id': employee.id,
                'name': employee.name,
                'job_title': employee.job_id.name,
                'attendance': attendance_info
            }

            return employee_info

        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}

    @http.route('/api/monitoring/employee/missed_days', type='json', auth='none', cors='*', csrf=False,
                methods=['POST'])
    def employee_missed_days(self, **kw):
        data = request.jsonrequest
        employee_id = data.get('employee_id')
        month = data.get('month')

        if not employee_id or not month:
            return {"error": "Os campos 'employee_id' e 'month' são obrigatórios."}

        try:
            month = int(month)
        except ValueError:
            return {"error": "O campo 'month' deve ser um inteiro válido."}

        if not 1 <= month <= 12:
            return {"error": "O campo 'month' deve estar entre 1 e 12."}

        year = datetime.now().year

        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)
        if not employee:
            return {"error": "Employee not found"}

        current_date = datetime.now().date()
        num_days = monthrange(year, month)[1]

        all_days = [
            datetime(year, month, day).date()
            for day in range(1, num_days + 1)
            if datetime(year, month, day).date() <= current_date
        ]

        attendance_records = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', datetime(year, month, 1)),
            ('check_in', '<', datetime(year, month, num_days) + timedelta(days=1))
        ])

        check_in_days = {record.check_in.date() for record in attendance_records if record.check_in}

        missed_days = [day.isoformat() for day in all_days if day not in check_in_days]

        response = {
            'id': employee.id,
            'name': employee.name,
            'job_title': employee.job_id.name,
            'missed_days': missed_days
        }

        return response

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

    @http.route('/api/data/employee/', type='http', auth='none', cors='*', csrf=False, methods=['POST'])
    def employee_data(self, **kw):
        data = request.jsonrequest
        employee_id = data.get('employee_id')
        attendance_datetime = data.get('datetime')



        Notification = request.env['attendance.notification'].sudo().create({
            'employee_id': employee_id,
            'check_in': attendance_datetime,
        })

        return Notification

    @http.route('/getimage_candidate/<int:employee_id>', type='http', auth='none', cors='*', csrf=False,
                methods=['GET'])
    def api_getimage_candidate(self, employee_id):
        if not employee_id:
            return request.make_response('{"error": "employee_id is required"}',
                                         headers=[('Content-Type', 'application/json')])

        employee = request.env['hr.employee'].sudo().search([('id', '=', int(employee_id))], limit=1)

        if not employee:
            return request.make_response('{"error": "employee_id not found"}',
                                         headers=[('Content-Type', 'application/json')])

        if employee.image_1920:
            image_data = base64.b64decode(employee.image_1920)
            headers = [('Content-Type', 'image/jpeg'), ('Content-Length', str(len(image_data)))]
            return request.make_response(image_data, headers=headers)

        return request.make_response('{"error": "No image found for this employee"}',
                                     headers=[('Content-Type', 'application/json')])

    @http.route('/notification/employee/', auth='none', cors='*', csrf=False, methods=['GET'])
    def employee_notification(self, **kw):
        records = request.env['attendance.notification'].sudo().search([])
        info_records = []

        for record in records:
            check_in = record.check_in.strftime('%Y-%m-%d') if record.check_in else None
            check_out = record.check_out.strftime('%Y-%m-%d') if record.check_out else None

            info_records.append({
                'employee_id': record.employee_id.id,
                'name': record.employee_id.name,
                'check_in': check_in,
                'check_out': check_out,
                'is_read': record.is_read,
            })

        return werkzeug.wrappers.Response(json.dumps(info_records), headers=[('Content-Type', 'application/json')])

    @http.route('/api/report/overtime', type='json', auth='none', cors='*', csrf=False, methods=['POST'])
    def overtime(self, **kw):
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

        present_employee_ids = attendances.mapped('employee_id.id')
        total_present = len(present_employee_ids)
        total_absent = total_employees - total_present

        present_employees = []
        absent_employees = []

        for employee in employees:
            if employee.id in present_employee_ids:
                present_employees.append({
                    'id': employee.id,
                    'name': employee.name
                })
            else:
                absent_employees.append({
                    'id': employee.id,
                    'name': employee.name
                })

        report_data = {
            'company_id': company_id,
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'counts': {
                'total_employees': total_employees,
                'total_present': total_present,
                'total_absent': total_absent
            },
            'present_employees': present_employees,
            'absent_employees': absent_employees
        }

        return report_data

    @http.route('/api/notification/read', type='json', auth='none', cors='*', csrf=False, methods=['POST'])
    def set_notification_read(self, **kw):
        data = request.jsonrequest
        notification_id = data.get('notification_id')
        is_read = data.get('is_read', False)

        if not notification_id:

            return {'error': 'Notification ID is required'}

        notification = request.env['attendance.notification'].sudo().search([('id', '=', notification_id)], limit=1)

        if not notification:
            return {'error': 'Notification not found'}

        notification.sudo().write({'is_read': is_read})

        return {
            'success': True,
            'message': 'Notification updated successfully',
            'notification_id': notification_id,
            'is_read': is_read
        }

    @http.route('/api/custom_response', type='json', auth='public', methods=['POST'])
    def custom_response(self, **kwargs):
        # Define tu respuesta personalizada
        response_data = {
            "status": "success",
            "message": "Esta es una respuesta personalizada",
            "data": kwargs
        }


        return Response(
            json.dumps(response_data),
            status=200,  # Código HTTP
            headers=[
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(json.dumps(response_data))))
            ]
        )
