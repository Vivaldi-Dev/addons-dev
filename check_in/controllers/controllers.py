import base64
from functools import wraps

from odoo import http
from odoo.addons.test_convert.tests.test_env import record
from odoo.http import Response
from calendar import monthrange
from odoo.http import request
import werkzeug
import json
from datetime import datetime, timedelta
import pytz

from odoo.addons.authmodel.controllers.decorators.token_required import token_required


class CheckIn(http.Controller):

    def coach_Administrator(func):
        @wraps(func)
        def wrapper(self, **kw):

            data = request.jsonrequest
            all_subordinates_ids = []
            company_id = None
            department_id = None

            if data:
                employee_id = data.get('employee_id')
                company_id = data.get('company_id')
                department_id = data.get('department_id')

                if employee_id:
                    Employee = request.env['hr.employee'].sudo()
                    employee = Employee.browse(int(employee_id))

                    if employee.exists():
                        user = employee.user_id
                        if user:
                            request.env.cr.commit()

                            domain = []
                            if company_id:
                                domain.append(('company_id', '=', int(company_id)))
                            if department_id:
                                domain.append(('department_id', '=', int(department_id)))

                            if user.has_group('check_in.group_hr_admin'):
                                all_subordinates_ids = Employee.search(domain).ids

                            elif user.has_group('check_in.group_hr_officer'):
                                all_subordinates_ids = employee.child_ids.filtered(
                                    lambda e: e.company_id.id == int(company_id)).ids

                                coached_employees = Employee.search([('coach_id', 'in', all_subordinates_ids)] + domain)
                                all_subordinates_ids += coached_employees.ids

            kw['all_subordinates_ids'] = all_subordinates_ids
            kw['company_id'] = company_id
            kw['department_id'] = department_id
            return func(self, **kw)

        return wrapper

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
    @coach_Administrator
    def presentes(self, **kw):
        try:
            data = request.jsonrequest

            if not data:
                return {'error': 'A requisição precisa conter dados.'}

            company_id = kw.get('company_id')
            department_id = kw.get('department_id')
            all_subordinates_ids = kw.get('all_subordinates_ids', [])

            if not company_id:
                return werkzeug.wrappers.Response(
                    json.dumps({'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            start_date = data.get('start_date')
            end_date = data.get('end_date')
            address_id = data.get('address_id')
            by_name = data.get('by_name')
            page = int(data.get('page', 1))
            limit = int(data.get('limit', 10))

            today = datetime.utcnow()

            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.combine(today,
                                                                                                           datetime.min.time())
                end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1,
                                                                               seconds=-1) if end_date else datetime.combine(
                    today, datetime.max.time())

                if start_date > end_date:
                    return {'error': 'A data inicial não pode ser posterior à data final.'}
            except ValueError:
                return {'error': 'Os campos "start_date" e "end_date" devem estar no formato "YYYY-MM-DD".'}

            domain = [
                ('company_id', '=', int(company_id)),
                ('id', 'in', all_subordinates_ids),
                ('device_id', '!=', False)
            ]

            if department_id:
                domain.append(('department_id', '=', int(department_id)))

            if by_name:
                domain.append(('name', 'ilike', by_name))

            employees = request.env['hr.employee'].sudo().search(domain)
            total_employees = len(employees)

            records = []
            presentes = 0

            tz_maputo = pytz.timezone('Africa/Maputo')
            tz_utc = pytz.utc

            for employee in employees:
                attendance_domain = [
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', start_date),
                    ('check_in', '<=', end_date)
                ]

                if address_id:
                    attendance_domain.append(('address_id', '=', int(address_id)))

                attendances = request.env['hr.attendance'].sudo().search(attendance_domain, order='check_in desc')

                for attendance in attendances:
                    check_in = attendance.check_in
                    check_out = attendance.check_out

                    check_in = check_in.replace(tzinfo=tz_utc).astimezone(tz_maputo).strftime(
                        '%Y-%m-%d %H:%M:%S') if check_in else ''
                    check_out = check_out.replace(tzinfo=tz_utc).astimezone(tz_maputo).strftime(
                        '%Y-%m-%d %H:%M:%S') if check_out else ''

                    records.append({
                        'id': employee.id,
                        'job_position': employee.job_title,
                        'name': employee.name,
                        'check_in': check_in,
                        'check_out': check_out,
                        'address_id': attendance.address_id.name,
                        'status': 'presente'
                    })
                    presentes += 1

            records = sorted(records, key=lambda x: max(x['check_in'], x['check_out']), reverse=True)

            start = (page - 1) * limit
            end = start + limit
            paginated_records = records[start:end]

            return {
                'total_employees': total_employees,
                'total_presentes': presentes,
                'page': page,
                'limit': limit,
                'total_pages': (len(records) + limit - 1) // limit,
                'records': paginated_records
            }

        except Exception as e:
            return {'error': str(e)}

    @token_required
    @http.route('/api/monitoring/ausentes', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    @coach_Administrator
    def ausentes(self, **kw):
        """
        Retorna a lista de funcionários ausentes com paginação.
        """
        try:
            data = request.jsonrequest

            if not data:
                return {'error': 'A requisição precisa conter dados.'}

            company_id = kw.get('company_id')
            department_id = kw.get('department_id')
            all_subordinates_ids = kw.get('all_subordinates_ids', [])

            if not company_id:
                return werkzeug.wrappers.Response(
                    json.dumps({'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )

            start_date = data.get('start_date')
            end_date = data.get('end_date')
            by_name = data.get('by_name')

            tz_maputo = pytz.timezone('Africa/Maputo')
            tz_utc = pytz.utc

            if start_date:
                try:
                    start_date = tz_maputo.localize(datetime.strptime(start_date, '%Y-%m-%d')).astimezone(tz_utc)
                except ValueError:
                    return {'error': 'O campo "start_date" deve estar no formato "YYYY-MM-DD".'}

            if end_date:
                try:
                    end_date = tz_maputo.localize(datetime.strptime(end_date, '%Y-%m-%d')).astimezone(tz_utc)
                    if start_date == end_date:
                        end_date = end_date + timedelta(hours=23, minutes=59, seconds=59)
                except ValueError:
                    return {'error': 'O campo "end_date" deve estar no formato "YYYY-MM-DD".'}

            if start_date and end_date and start_date > end_date:
                return {'error': 'A data inicial não pode ser posterior à data final.'}

            domain = [
                ('company_id', '=', int(company_id)),
                ('id', 'in', all_subordinates_ids),
                ('device_id', '!=', False)
            ]

            if department_id:
                domain.append(('department_id', '=', int(department_id)))

            if by_name:
                domain.append(('name', 'ilike', by_name))

            employees = request.env['hr.employee'].sudo().search(domain)
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
                    ('check_in', '<=', end_date) if end_date else ()
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
    @coach_Administrator
    def absentens(self, **kw):
        data = request.jsonrequest

        if not data:
            return {'error': 'A requisição precisa conter dados.'}

        company_id = kw.get('company_id')
        department_id = kw.get('department_id')
        all_subordinates_ids = kw.get('all_subordinates_ids', [])

        if not company_id:
            return {'error': 'O campo "company_id" é obrigatório.'}

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

        domain = [
            ('state', 'in', ['confirm', 'refuse', 'validate']),
            ('employee_id.company_id', '=', int(company_id)),
            ('employee_id', 'in', all_subordinates_ids),
            ('employee_id.device_id', '!=', False)
        ]

        if department_id:
            domain.append(('employee_id.department_id', '=', int(department_id)))

        if by_name:
            domain.append(('employee_id.name', 'ilike', by_name))

        if start_date:
            domain.append(('date_from', '>=', start_date))
        if end_date:
            domain.append(('date_to', '<=', end_date))

        state_mapping = {
            'draft': 'Para Enviar',
            'confirm': 'Para Aprovação',
            'refuse': 'Recusado',
            'validate1': 'Segunda Aprovação',
            'validate': 'Aprovado'
        }

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

    @http.route('/api/monitoring/percentages', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def percentages(self, **kw):
        try:
            data = request.jsonrequest
            company_id = data.get('company_id')

            if not company_id:
                return {'error': "'company_id' é obrigatório"}

            today = datetime.today().date()
            first_day_of_month = today.replace(day=1)
            last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)

            employees = request.env['hr.employee'].sudo().search([
                ('company_id', '=', int(company_id)),
                ('device_id', '!=', False),
            ])
            total_employees = len(employees)

            if total_employees == 0:
                return Response(
                    json.dumps({'error': 'Nenhum funcionário encontrado para a companhia fornecida'}),
                    content_type='application/json',
                    status=400
                )

            def calcular_presenca(data_inicio, data_fim):
                presentes = 0
                for employee in employees:
                    attendance = request.env['hr.attendance'].sudo().search([
                        ('employee_id', '=', employee.id),
                        ('check_in', '>=', datetime.combine(data_inicio, datetime.min.time())),
                        ('check_in', '<=', datetime.combine(data_fim, datetime.max.time()))
                    ])
                    if attendance:
                        presentes += 1

                ausentes = total_employees - presentes
                percentage_presentes = round((presentes / total_employees) * 100) if total_employees > 0 else 0
                percentage_ausentes = 100 - percentage_presentes

                return {
                    "total_employees": total_employees,
                    "presentes": presentes,
                    "ausentes": ausentes,
                    "percentage_presentes": f"{percentage_presentes}%",
                    "percentage_ausentes": f"{percentage_ausentes}%"
                }

            response_data = {
                "company_id": company_id,
                "data": {
                    "day": {
                        "date_range": {
                            "start": today.isoformat(),
                            "end": today.isoformat()
                        },
                        **calcular_presenca(today, today)
                    },
                    "week": {
                        "date_range": {
                            "start": start_of_week.isoformat(),
                            "end": end_of_week.isoformat()
                        },
                        **calcular_presenca(start_of_week, end_of_week)
                    },
                    "month": {
                        "date_range": {
                            "start": first_day_of_month.isoformat(),
                            "end": last_day_of_month.isoformat()
                        },
                        **calcular_presenca(first_day_of_month, last_day_of_month)
                    }
                }
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

            employees = request.env['hr.employee'].sudo().search([
                ('device_id', '!=', False)
            ])
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

        employees = request.env['hr.employee'].sudo().search([
            ('company_id', '=', company_id),
            ('device_id', '!=', False)
        ])

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

                tolerance_time = timedelta(minutes=10)
                expected_time_with_tolerance = datetime.combine(today, expected_time) + tolerance_time
                expected_time_with_tolerance = expected_time_with_tolerance.time()

                is_late = check_in_time > expected_time_with_tolerance

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
    @http.route('/company/company', type="json", auth='none', cors='*', csrf=False, methods=['POST'])
    def company(self):
        try:
            data = request.jsonrequest

            user_id = data.get('user_id')
            if not user_id:
                return {"error": "O campo 'user_id' é obrigatório no corpo da requisição."}

            user = request.env['res.users'].sudo().search([('id', '=', int(user_id))], limit=1)
            if not user:
                return {"error": "Usuário não encontrado."}

            allowed_company_ids = user.company_ids.ids

            companies = request.env['res.company'].sudo().search([('id', 'in', allowed_company_ids)])
            info = [{
                'id': company.id,
                'name': company.name,
            } for company in companies]

            return info

        except Exception as e:
            return {"error": f"Erro inesperado: {str(e)}"}

    @http.route('/api/overtime', auth='none', type="json", cors='*', csrf=False, methods=['GET'])
    def overtime(self):

        employees = request.env['hr.employee'].sudo().search([
            ('device_id', '!=', False)
        ])
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
    @coach_Administrator
    def get_employees_by_company(self, **kw):
        """
        Retorna a contagem de funcionários gerenciados pelo coach em uma empresa específica.
        """
        try:
            data = request.jsonrequest
            company_id = data.get('company_id')

            if not company_id:
                return {'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}

            all_subordinates_ids = kw.get('all_subordinates_ids', [])
            employees_count = request.env['hr.employee'].sudo().search_count([
                ('company_id', '=', int(company_id)),
                ('id', 'in', all_subordinates_ids),
                ('device_id', '!=', False),
            ])

            return {'employees_count': employees_count}

        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/monitoring/monitoring', auth='none', type="json", cors='*', csrf=False, methods=['POST'])
    def daily_overtime_check(self, **kw):
        data = request.jsonrequest

        if not data or 'company_id' not in data:
            return {'error': 'O campo "company_id" é obrigatório.'}

        company_id = data['company_id']

        employees = request.env['hr.employee'].sudo().search([
            ('company_id', '=', company_id),
            ('device_id', '!=', False)
        ])

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

    @http.route("/api/all/employees", auth='public', type="json", methods=['POST'], csrf=False)
    @coach_Administrator
    def all_employees(self, **kwargs):
        data = request.jsonrequest

        company_id = kwargs.get('company_id')
        if not company_id:
            return {'error': 'O parâmetro "company_id" é obrigatório.'}

        try:
            company_id = int(company_id)
        except ValueError:
            return {'error': 'O parâmetro "company_id" deve ser um número inteiro válido.'}

        all_subordinates_ids = kwargs.get('all_subordinates_ids', [])
        department_id = kwargs.get('department_id')
        domain = [
            ('company_id', '=', company_id),
            ('id', 'in', all_subordinates_ids),
            ('device_id', '!=', False),
        ]

        if department_id:
            try:
                department_id = int(department_id)
                domain.append(('department_id', '=', department_id))
            except ValueError:
                return {'error': 'O parâmetro "department_id" deve ser um número inteiro válido.'}

        if 'employee_id' in kwargs:
            try:
                employee_id = int(kwargs['employee_id'])
                domain.append(('id', '=', employee_id))
            except ValueError:
                return {'error': 'O parâmetro "employee_id" deve ser um número inteiro válido.'}

        if 'name' in data:
            domain.append(('name', 'ilike', data['name']))

        if 'x_ativo' in kwargs:
            x_ativo = data['x_ativo'].lower() in ['true', '1', 't']
            domain.append(('x_ativo', '=', x_ativo))

        try:
            limit = int(data.get('limit', 10))
            page = int(data.get('page', 1))
        except ValueError:
            return {'error': 'Os parâmetros "limit" e "page" devem ser números inteiros válidos.'}

        offset = (page - 1) * limit

        employees = request.env['hr.employee'].sudo().search(domain, offset=offset, limit=limit)

        total_count = request.env['hr.employee'].sudo().search_count(domain)

        if not employees:
            if offset >= total_count:
                employees = []

        if not employees:
            return {'data': [],
                    'pagination': {'total_records': total_count, 'total_pages': (total_count + limit - 1) // limit,
                                   'current_page': page, 'records_per_page': limit}}

        data_info = [
            {
                'id': employee.id,
                'name': employee.name,
                'email': employee.user_id.login if employee.user_id else '',
                'x_ativo': employee.x_ativo,
            }
            for employee in employees
        ]

        response_data = {
            'data': data_info,
            'pagination': {
                'total_records': total_count,
                'total_pages': (total_count + limit - 1) // limit,
                'current_page': page,
                'records_per_page': limit,
            }
        }

        return response_data

    @http.route('/api/employees', type='json', auth='none', methods=['PUT'], csrf=False)
    @coach_Administrator
    def update_employee_notifications(self, **kw):
        """
        Atualiza o campo x_ativo dos funcionários gerenciados pelo coach.
        """
        data = request.jsonrequest
        employee_ids = data.get('employee_ids', [])
        x_ativo = data.get('is_active')

        if not employee_ids:
            return {'status': 'error', 'message': 'Os IDs dos funcionários devem ser uma lista de inteiros.',
                    'data': data}

        if not isinstance(x_ativo, bool):
            return {'status': 'error', 'message': 'O valor de "x_ativo" deve ser um booleano.', 'data': data}

        all_subordinates_ids = kw.get('all_subordinates_ids', [])
        employees = request.env['hr.employee'].sudo().browse(employee_ids).filtered(
            lambda emp: emp.id in all_subordinates_ids
        )

        non_existing_employees = [emp_id for emp_id in employee_ids if emp_id not in employees.ids]
        if non_existing_employees:
            return {'status': 'error',
                    'message': f'Funcionários com IDs {non_existing_employees} não encontrados ou não são gerenciados por você.',
                    'data': data}

        employees.write({'x_ativo': x_ativo})

        return {'status': 'success', 'message': 'Notificação em tempo real atualizada com sucesso.', 'data': data}

    @http.route('/api/employees_avtive', type='json', auth='none', methods=['POST'], csrf=False)
    @coach_Administrator
    def employees_active(self, **kw):
        """
        Retorna uma lista de funcionários ativos (x_ativo=True) gerenciados pelo coach.
        """
        data = request.jsonrequest

        if not data or 'company_id' not in data:
            return {'error': 'O campo "company_id" é obrigatório.'}

        company_id = data['company_id']

        all_subordinates_ids = kw.get('all_subordinates_ids', [])
        employees = request.env['hr.employee'].sudo().search([
            ('company_id', '=', company_id),
            ('x_ativo', '!=', False),
            ('id', 'in', all_subordinates_ids)
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

            employee = request.env['hr.employee'].sudo().search([
                ('id', '=', employee_id),
                ('device_id', '!=', False)
            ], limit=1)

            if not employee:
                return {"error": "Employee not found"}

            next_month = month + 1 if month < 12 else 1
            next_month_year = current_year if month < 12 else current_year + 1

            maputo_tz = pytz.timezone('Africa/Maputo')

            start_date = maputo_tz.localize(datetime(current_year, month, 1))
            end_date = maputo_tz.localize(datetime(next_month_year, next_month, 1))

            attendance_records = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', start_date.astimezone(pytz.utc)),
                ('check_in', '<', end_date.astimezone(pytz.utc))
            ])

            attendance_info = [{
                'check_in': record.check_in.astimezone(maputo_tz).strftime(
                    '%Y-%m-%d %H:%M:%S') if record.check_in else None,
                'check_out': record.check_out.astimezone(maputo_tz).strftime(
                    '%Y-%m-%d %H:%M:%S') if record.check_out else None
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

        leave_records = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee_id),
            ('date_from', '>=', datetime(year, month, 1)),
            ('date_from', '<', datetime(year, month + 1, 1)),
            ('employee_id.device_id', '!=', False)
        ])

        missed_days_info = [
            {
                'date': leave.date_from.date(),
                'description': leave.name
            }
            for leave in leave_records
        ]

        return {
            'employee_id': employee_id,
            'month': month,
            'missed_days_info': missed_days_info
        }

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

    @http.route('/getimage_compony/<int:company_id>', auth='none', cors='*', csrf=False, methods=['GET'])
    def api_getimage_component(self, company_id):

        if not company_id:
            response = request.make_response('{"error": "company_id not found"}',
                                             headers=[('Content-Type', 'application/json')])
            response.status_code = 400
            return response

        company = request.env['res.company'].sudo().search([('id', '=', company_id)], limit=1)
        if not company:
            response = request.make_response('{"error": "company_id not found"}',
                                             headers=[('Content-Type', 'application/json')])
            response.status_code = 404
            return response

        if company.logo:
            try:
                image_data = base64.b64decode(company.logo)
                headers = [('Content-Type', 'image/jpeg'), ('Content-Length', str(len(image_data)))]
                return request.make_response(image_data, headers=headers)
            except Exception as e:
                response = request.make_response(f'{{"error": "Failed to decode image: {str(e)}"}}',
                                                 headers=[('Content-Type', 'application/json')])
                response.status_code = 500
                return response

        response = request.make_response('{"error": "No image found for this company"}',
                                         headers=[('Content-Type', 'application/json')])
        response.status_code = 404
        return response

    @http.route('/notification/employeess/', auth='none', cors='*', csrf=False, methods=['GET'])
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

    @http.route('/notification/employee/', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    @coach_Administrator
    def employee_notification(self, **kw):
        """
        Retorna as notificações de presença dos funcionários gerenciados pelo coach.
        As datas são convertidas para o fuso horário da África/Maputo.
        """
        all_subordinates_ids = kw.get('all_subordinates_ids', [])

        records = request.env['attendance.notification'].sudo().search([
            ('employee_id', 'in', all_subordinates_ids)
        ])

        maputo_tz = pytz.timezone('Africa/Maputo')

        info_records = []
        for record in records:
            check_in = None
            if record.check_in:
                check_in_utc = pytz.utc.localize(record.check_in)
                check_in = check_in_utc.astimezone(maputo_tz).strftime('%Y-%m-%d %H:%M')

            check_out = None
            if record.check_out:
                check_out_utc = pytz.utc.localize(record.check_out)
                check_out = check_out_utc.astimezone(maputo_tz).strftime('%Y-%m-%d %H:%M')

            info_records.append({
                'employee_id': record.employee_id.id,
                'name': record.employee_id.name,
                'check_in': check_in,
                'check_out': check_out,
                'is_read': record.is_read,
            })

        return info_records

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

        response_data = {
            "status": "success",
            "message": "Esta es una respuesta personalizada",
            "data": kwargs
        }

        return Response(
            json.dumps(response_data),
            status=200,
            headers=[
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(json.dumps(response_data))))
            ]
        )

    @http.route('/api/custom_response/', type='json', auth='public', methods=['POST'])
    @coach_Administrator
    def custom_response(self, **kwargs):
        """
        Retorna as notificações de um funcionário gerenciado pelo coach.
        """
        data = request.jsonrequest

        employee_id = data.get('id')
        if not employee_id:
            return {'error': 'O campo "id" é obrigatório.'}

        all_subordinates_ids = kwargs.get('all_subordinates_ids', [])
        if int(employee_id) not in all_subordinates_ids:
            return {
                'error': f'Você não tem permissão para acessar as notificações do funcionário com ID {employee_id}.'}

        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)

        if not employee:
            return {'error': f'Funcionário com ID {employee_id} não encontrado.'}

        notifications = request.env['attendance.notification'].sudo().search([
            ('employee_id', '=', employee.id)
        ])
        notifications_info = []

        for notification in notifications:
            notifications_info.append({
                'id': notification.id,
                'name': notification.employee_id.name,
                'is_read': notification.is_read,
                'check_in': notification.check_in.strftime('%Y-%m-%d') if notification.check_in else 'N/A',
                'check_out': notification.check_out.strftime('%Y-%m-%d') if notification.check_out else 'N/A',
            })

        return notifications_info

    @http.route('/api/week/', type='http', auth='public', methods=['GET'])
    def week(self, **kwargs):

        records = request.env['hr.employee'].sudo().search([
            ('device_id', '!=', False)
        ])

        info_employees = []
        for employee in records:

            attendance_ids = employee.resource_calendar_id.attendance_ids
            attendance_info = []

            if attendance_ids:

                for attendance in attendance_ids:
                    attendance_info.append({
                        'id': attendance.id,
                        'name': attendance.name,
                        'hour_from': attendance.hour_from,
                        'hour_to': attendance.hour_to,
                    })

                info_employees.append({
                    'employee_id': employee.id,
                    'name': employee.name,
                    'attendance_info': attendance_info,
                })
            else:

                info_employees.append({
                    'id': employee.id,
                    'name': employee.name,
                    'attendance_info': [],
                })

        return werkzeug.wrappers.Response(
            json.dumps(info_employees),
            headers={'Content-Type': 'application/json'},
            status=200
        )

    @http.route('/api/time_off/', type='http', auth='public', methods=['GET'])
    def time_off(self, **kwargs):

        records = request.env['hr.leave'].sudo().search([])

        info_employees = []

        for holy in records:
            info_employees.append({
                'employee_id': holy.employee_id.name,
                'holiday_status_id': holy.holiday_status_id.name,
                'leave_type': holy.holiday_status_id.leave_type,
                'code': holy.holiday_status_id.code,
                'date_from': holy.date_from.strftime('%Y-%m-%d'),
                'date_to': holy.date_to.strftime('%Y-%m-%d'),
                'state': holy.state,
            })
        return werkzeug.wrappers.Response(json.dumps(info_employees), headers={'Content-Type': 'application/json'})

    @http.route('/api/set_timezone/', type='json', auth='public', methods=['POST'])
    def set_timezone(self, **kwargs):
        data = request.jsonrequest

        if not data:
            return {"status": "error", "message": "Preencha todos os campos."}

        employee_id = data.get('employee_id')
        check_in = data.get('check_in')
        check_out = data.get('check_out')

        if not employee_id or not check_in or not check_out:
            return {"status": "error", "message": "Os campos employee_id, check_in e check_out são obrigatórios."}

        try:

            maputo_tz = pytz.timezone("Africa/Maputo")
            utc_tz = pytz.utc

            check_in_dt = maputo_tz.localize(datetime.strptime(check_in, "%Y-%m-%d %H:%M:%S"))
            check_out_dt = maputo_tz.localize(datetime.strptime(check_out, "%Y-%m-%d %H:%M:%S"))

            check_in_dt_utc = check_in_dt.astimezone(utc_tz).replace(tzinfo=None)
            check_out_dt_utc = check_out_dt.astimezone(utc_tz).replace(tzinfo=None)

        except ValueError:
            return {"status": "error", "message": "Formato de data inválido. Use 'YYYY-MM-DD HH:MM:SS'"}

        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)

        if not employee:
            return {"status": "error", "message": "employee_id não encontrado."}

        attendance = request.env['hr.attendance'].sudo().create({
            'employee_id': employee.id,
            'check_in': check_in_dt_utc,
            'check_out': check_out_dt_utc,
        })

        return {
            "status": "success",
            "message": "Registro de atendimento criado com sucesso.",
            "attendance_id": attendance.id
        }

    @http.route('/api/set_timezones/', type='json', auth='public', methods=['POST'])
    def set_timezones(self, **kwargs):
        data = request.jsonrequest

        if not data:
            return {"status": "error", "message": "Preencha todos os campos."}

        employee_id = data.get('employee_id')
        check_in = data.get('check_in')
        check_out = data.get('check_out')

        if not employee_id or not check_in or not check_out:
            return {"status": "error", "message": "Os campos employee_id, check_in e check_out são obrigatórios."}

    @http.route('/api/_look_for_fouls/', type='json', auth='public', methods=['POST'])
    def look_for_fouls(self, **kwargs):
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

        if start_date > end_date:
            return {'error': "'date_from' não pode ser maior que 'date_to'"}

        leaves = request.env['hr.leave'].sudo().search([
            ('date_from', '<=', end_date),
            ('date_to', '>=', start_date),
            ('state', 'in', ['confirm', 'refuse']),
            ('employee_id.company_id', '=', int(company_id))
        ])

        employee_ids = leaves.mapped('employee_id.id')
        absence_count = len(set(employee_ids))

        return {
            'company_id': company_id,
            'date_from': date_from,
            'date_to': date_to,
            'absent_employees_count': absence_count
        }

    @http.route('/api/address_id/', auth='public', methods=['GET'])
    def get_address_id(self, **kwargs):
        record = request.env['zk.machine'].sudo().search([])
        info = []

        for record in record:
            info.append({
                'id': record.address_id.id,
                'address_id': record.address_id.name,
            })

        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)

    @http.route('/api/report/overtime', type='json', auth='none', cors='*', csrf=False, methods=['POST'])
    @coach_Administrator
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

            all_subordinates_ids = kw.get('all_subordinates_ids', [])
            department_id = kw.get('department_id')
            domain = [
                ('company_id', '=', company_id),
                ('id', 'in', all_subordinates_ids),
                ('device_id', '!=', False)
            ]

            if department_id:
                try:
                    department_id = int(department_id)
                    domain.append(('department_id', '=', department_id))
                except ValueError:
                    return {'error': 'O parâmetro "department_id" deve ser um número inteiro válido.'}

            employees = request.env['hr.employee'].sudo().search(domain)
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

    @http.route('/api/monitoring/employee/checkin_summary', auth='public', type='json', methods=['POST'])
    def employee_report(self, **kwargs):
        try:
            maputo_tz = pytz.timezone('Africa/Maputo')

            data = request.jsonrequest
            employee_id = data.get('employee_id')
            month = data.get('month')
            year = data.get('year')

            state_mapping = {
                'draft': 'Por Enviar',
                'confirm': 'Por Aprovar',
                'refuse': 'Recusado',
                'validate1': 'Segunda Aprovação',
                'validate': 'Aprovado'
            }

            if not employee_id or not month or not year:
                return {'error': 'Employee ID, month, and year are required'}

            try:
                month = int(month)
                year = int(year)
            except ValueError:
                return {'error': 'Month and year must be numeric'}

            if month < 1 or month > 12:
                return {'error': 'Invalid month. Use values between 1 and 12'}

            today = datetime.now(maputo_tz)
            last_day_of_month = (datetime(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            start_date = maputo_tz.localize(datetime(year, month, 1))
            end_date = maputo_tz.localize(last_day_of_month)

            if year == today.year and month == today.month:
                end_date = today

            employee = request.env['hr.employee'].sudo().search([
                ('id', '=', employee_id),
                ('device_id', '!=', False)
            ], limit=1)

            if not employee:
                return {"error": "Employee not found"}

            resource_calendar = employee.resource_calendar_id
            if not resource_calendar:
                return {"error": "Calendário de trabalho não encontrado para o funcionário."}

            def is_work_day(day_date):
                day_of_week = day_date.weekday()
                for attendance in resource_calendar.attendance_ids:
                    if int(attendance.dayofweek) == day_of_week:
                        return True
                return False

            total_work_days_until_now = 0
            current_date = start_date
            while current_date <= end_date:
                if is_work_day(current_date.date()):
                    total_work_days_until_now += 1
                current_date += timedelta(days=1)

            leave_records = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee_id),
                ('date_from', '>=', start_date.astimezone(pytz.utc)),
                ('date_from', '<=', end_date.astimezone(pytz.utc))
            ])

            missed_days_info = []
            for leave in leave_records:
                leave_date = leave.date_from.astimezone(maputo_tz).date()
                missed_days_info.append({
                    'employee_name': employee.name,
                    'date': leave_date.strftime('%Y-%m-%d'),
                    'description': leave.sudo().private_name if leave.sudo().private_name else 'Descrição não fornecida',
                    'state': state_mapping.get(leave.state, leave.state),
                })

            attendance_records = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id),
                ('check_in', '>=', start_date.astimezone(pytz.utc)),
                ('check_in', '<=', end_date.astimezone(pytz.utc))
            ])

            attendance_info = [
                {
                    'employee_name': employee.name,
                    'date': attendance.check_in.astimezone(maputo_tz).date().strftime('%Y-%m-%d'),
                    'check_in': attendance.check_in.astimezone(maputo_tz).strftime('%Y-%m-%d %H:%M:%S'),
                    'check_out': attendance.check_out.astimezone(maputo_tz).strftime(
                        '%Y-%m-%d %H:%M:%S') if attendance.check_out else None,
                    'address_id': attendance.address_id.name,
                }
                for attendance in attendance_records
            ]

            present_days = set()
            for attendance in attendance_records:
                attendance_date = attendance.check_in.astimezone(maputo_tz).date()
                present_days.add(attendance_date)

            total_present_days = len(present_days)
            total_missed_days = len(missed_days_info)

            return {
                'employee_id': employee_id,
                'employee_name': employee.name,
                'month': month,
                'year': year,
                'total_days_until_now': total_work_days_until_now,
                'total_present_days': total_present_days,
                'total_missed_days': total_missed_days,
                'missed_days_info': missed_days_info,
                'attendance_info': attendance_info
            }

        except Exception as e:
            return {'error': str(e)}

    @http.route('/api/report/', auth='public', type='json', methods=['POST'])
    def report(self, **kwargs):
        data = request.jsonrequest
        company_id = data.get('company_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not company_id or not start_date or not end_date:
            return {'error': 'Company ID, start_date e end_date são obrigatórios'}

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return {'error': 'Formato de data inválido. Use YYYY-MM-DD'}

        if start_date > end_date:
            return {'error': 'A data de início deve ser antes da data de fim'}

        current_year = datetime.now().year
        current_month = datetime.now().month

        if start_date.year == current_year or end_date.year == current_year:
            if end_date.month > current_month:
                return {'error': 'Não é possível solicitar um relatório para meses futuros no ano atual'}

        employees = request.env['hr.employee'].sudo().search([('company_id', '=', company_id)])
        total_employees = len(employees)

        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', 'in', employees.ids),
            ('check_in', '>=', start_date.strftime("%Y-%m-%d 00:00:00")),
            ('check_in', '<=', end_date.strftime("%Y-%m-%d 23:59:59")),
        ])

        attendance_dict = {}
        for att in attendances:
            employee_id = att.employee_id.id
            check_in_date = att.check_in.date()
            key = (employee_id, check_in_date)

            if key not in attendance_dict or att.check_in > attendance_dict[key].check_in:
                attendance_dict[key] = att

        present_list = []
        present_employee_ids = set()
        for att in attendance_dict.values():
            present_list.append({
                'employee_id': att.employee_id.id,
                'name': att.employee_id.name,
                'check_in': att.check_in.strftime("%Y-%m-%d %H:%M:%S") if att.check_in else "",
                'check_out': att.check_out.strftime("%Y-%m-%d %H:%M:%S") if att.check_out else "Ainda no trabalho"
            })
            present_employee_ids.add(att.employee_id.id)

        present_employees = len(present_list)
        absent_employees = total_employees - len(
            present_employee_ids)

        absent_list = []
        for emp in employees:
            if emp.id not in present_employee_ids:
                absent_list.append({
                    'employee_id': emp.id,
                    'name': emp.name
                })

        return {
            'company_id': company_id,
            'start_date': start_date.strftime("%Y-%m-%d"),
            'end_date': end_date.strftime("%Y-%m-%d"),
            'total_employees': total_employees,
            'present_employees': present_employees,
            'absent_employees': absent_employees,
            'present_list': present_list,
            'absent_list': absent_list
        }

    @http.route('/api/report_attendance/', auth='public', methods=['GET'])
    def report_attendance(self, **kwargs):
        record = request.env['hr.attendance'].sudo().search([])
        info = []

        for i in record:
            info.append({
                'employee_id': i.employee_id.name,
                'check_in': i.check_in.strftime("%Y-%m-%d ") if i.check_in else "",
                'check_out': i.check_out.strftime("%Y-%m-%d ") if i.check_out else "",
            })
        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)

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

    @http.route('/api/employees/by_coach', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def employees_by_coach(self, **kw):
        data = request.jsonrequest

        if not data:
            return {'error': 'A requisição precisa conter dados.'}

        coach_id = data.get('employee_id')
        if not coach_id:
            return {'error': 'O campo "employee_id" é obrigatório no corpo da requisição.'}

        Employee = request.env['hr.employee'].sudo()
        employees = Employee.search([('coach_id', '=', int(coach_id))])

        result = []
        for employee in employees:
            result.append({
                'employee_id': employee.id,
                'employee_name': employee.name,
                'job_position': employee.job_id.name,
                'department': employee.department_id.name,
                'work_email': employee.work_email,
                'work_phone': employee.work_phone
            })

        return {'coached_employees': result}

    @http.route('/api/attendance/last_records', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    @coach_Administrator
    def last_attendance_records(self, **kwargs):
        data = request.jsonrequest

        company_id = kwargs.get('company_id')

        if not data:
            return {'error': 'A requisição precisa conter dados.'}

        if not company_id:
            return {'error': 'O campo "company_id" é obrigatório no corpo da requisição.'}

        company_tz = pytz.timezone('Africa/Maputo')

        limit = int(data.get('limit', 10))
        all_subordinates_ids = kwargs.get('all_subordinates_ids', [])
        department_id = kwargs.get('department_id')

        today_utc = datetime.now(pytz.utc)
        today_maputo = today_utc.astimezone(company_tz).date()
        today_start = datetime.combine(today_maputo, datetime.min.time()).astimezone(company_tz)
        today_start_utc = today_start.astimezone(pytz.utc)

        domain = [
            ('employee_id.company_id', '=', int(company_id)),
            ('employee_id', 'in', all_subordinates_ids),
            '|',
            ('check_in', '>=', today_start_utc),
            ('check_out', '>=', today_start_utc),
            ('employee_id.device_id', '!=', False)
        ]

        if department_id:
            try:
                department_id = int(department_id)
                domain.append(('employee_id.department_id', '=', department_id))
            except ValueError:
                return {'error': 'O parâmetro "department_id" deve ser um número inteiro válido.'}

        records = request.env['hr.attendance'].sudo().search(domain, limit=limit)

        sorted_records = sorted(records, key=lambda r: max(r.check_in or datetime.min, r.check_out or datetime.min),
                                reverse=True)

        attendance_records = []
        for record in sorted_records:
            check_in_maputo = record.check_in.astimezone(company_tz) if record.check_in else None
            check_out_maputo = record.check_out.astimezone(company_tz) if record.check_out else None

            attendance_records.append({
                'employee_id': record.employee_id.id,
                'employee_name': record.employee_id.name,
                'check_in': check_in_maputo.strftime('%Y-%m-%d %H:%M:%S') if check_in_maputo else None,
                'check_out': check_out_maputo.strftime('%Y-%m-%d %H:%M:%S') if check_out_maputo else None
            })

        return {'attendance_records': attendance_records}

    @http.route('/api/employee/update_notifications', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def update_notifications(self, **kwargs):
        data = request.jsonrequest

        if not data:
            return {'error': 'Nenhum dado fornecido.'}

        employee_id = data.get('employee_id')
        notify_employee_ids = data.get('notify_employee_ids', [])
        action = data.get('action', 'add')

        if not employee_id:
            return {'error': 'O campo "employee_id" é obrigatório.'}

        if action not in ['add', 'remove']:
            return {'error': 'Ação inválida. Use "add" para adicionar ou "remove" para remover notificações.'}

        employee = request.env['hr.employee'].sudo().browse(int(employee_id))
        if not employee.exists():
            return {'error': f'Funcionário com ID {employee_id} não encontrado.'}

        notify_employees = request.env['hr.employee'].sudo().browse(notify_employee_ids)

        if not notify_employees:
            return {'error': 'Nenhum funcionário válido encontrado em notify_employee_ids.'}

        try:
            for notify_employee in notify_employees:
                existing_notifications = notify_employee.notify_employee_ids.ids

                if action == 'add':
                    if employee_id not in existing_notifications:
                        updated_notifications = existing_notifications + [employee_id]
                        notify_employee.write({'notify_employee_ids': [(6, 0, updated_notifications)]})

                elif action == 'remove':
                    if employee_id in existing_notifications:
                        updated_notifications = [eid for eid in existing_notifications if eid != employee_id]
                        notify_employee.write({'notify_employee_ids': [(6, 0, updated_notifications)]})

            return {
                'success': True,
                'message': f'Notificações atualizadas com sucesso ({action}).',
                'notify_employee_ids': notify_employee_ids
            }
        except Exception as e:
            return {'error': f'Erro ao atualizar notificações: {str(e)}'}

    @http.route('/api/employee/get_notifications', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def get_notifications(self, ):

        data = request.jsonrequest

        if not data:
            return {'error': 'Nenhum dado fornecido.'}

        employee_id = data.get('employee_id')

        if not employee_id:
            return {'error': 'O campo "employee_id" é obrigatório.'}

        try:
            employee_id = int(employee_id)

            employees = request.env['hr.employee'].sudo().search([
                ('notify_employee_ids', 'in', [employee_id]),
                ('device_id', '!=', False)
            ])

            if not employees:
                return {'message': f'Nenhum funcionário encontrado notificando o employee_id {employee_id}.'}

            employee_list = [{
                'id': emp.id,
                'name': emp.name,

            } for emp in employees]

            return {
                'success': True,
                'message': "",
                'employee_id': employee_id,
                'notify_employee_ids': employee_list
            }

        except ValueError:
            return {'error': 'O campo "employee_id" deve ser um número válido.'}
        except Exception as e:
            return {'error': f'Erro ao buscar notificações: {str(e)}'}

    @http.route('/api/childs', auth='none', type='json', cors='*', csrf=False, methods=['POST'])
    def get_childs(self):
        data = request.jsonrequest
        if not data:
            return {'error': 'Nenhum dado fornecido.'}

        employee_id = data.get('employee_id')
        if not employee_id:
            return {'error': 'employee_id é obrigatório.'}

        Employee = request.env['hr.employee'].sudo()
        record = Employee.browse(int(employee_id))
        if not record.exists():
            return {'error': 'Nenhum dado encontrado.'}

        all_subordinates_ids = record.child_ids.ids

        coached_employee_ids = Employee.search([('coach_id', '=', record.id)]).ids

        all_subordinates_ids += coached_employee_ids

        all_employees = Employee.browse(all_subordinates_ids)

        child_count = len(all_employees)

        return {
            'id': record.id,
            'name': record.name,
            'child_ids': [{'id': emp.id, 'name': emp.name} for emp in all_employees],
            'child_count': child_count
        }

    @http.route('/api/company/departments', type='json', auth='none', cors='*', csrf=False, methods=['POST'])
    @coach_Administrator
    def get_company_departments(self, **kwargs):
        try:
            data = request.jsonrequest

            if not data:
                return {"error": "A requisição precisa conter um corpo JSON válido."}

            company_id = data.get('company_id')
            if not company_id:
                return {"error": 'O campo "company_id" é obrigatório.'}

            all_subordinates_ids = kwargs.get('all_subordinates_ids', [])

            if not all_subordinates_ids:
                return {"error": "Nenhum subordinado encontrado para o funcionário."}

            departments = request.env['hr.department'].sudo().search([
                ('company_id', '=', int(company_id)),
                ('member_ids', 'in', all_subordinates_ids)
            ])

            unique_departments = departments.filtered(lambda d: d.id in departments.ids)

            department_list = [{
                'id': dept.id,
                'name': dept.name,
                'manager': dept.manager_id.name if dept.manager_id else None
            } for dept in unique_departments]

            return department_list

        except Exception as e:
            return {"error": str(e)}

    @http.route('/api/release', type='http', auth='public', methods=['GET'], csrf=False)
    def release_info(self, **kwargs):
        records = request.env['js_version_pontual.js_version_pontual'].sudo().search([])
        info = []

        if not records:
            werkzeug.wrappers.Response(json.dumps(
                {
                    "success": False,
                    "message": "Nenhum dado encontrado.",
                }
            ), status=404)

        for record in records:
            info.append({
                'id': record.id,
                'version': record.version,
                'create_date': record.create_date.strftime('%d/%m/%Y'),
            })
        return werkzeug.wrappers.Response(json.dumps(info), headers={'Content-Type': 'application/json'}, status=200)
