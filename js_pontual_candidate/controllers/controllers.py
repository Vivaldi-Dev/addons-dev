# -*- coding: utf-8 -*-
import asyncio
import base64
import calendar
import json
import traceback
from datetime import datetime, time, timedelta
import re
from pydub import AudioSegment
import io

import websockets
from websockets import uri

from odoo.addons.portal.controllers import web

from odoo import http
import werkzeug

from odoo.addons.test_convert.tests.test_env import record
from odoo.exceptions import ValidationError, UserError
from odoo.http import request, HttpRequest, Response, _logger, content_disposition
from odoo.addons.authmodel.controllers.decorators.token_required import token_required
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import pytz

active_websockets = []


class JsPontualCandidate(http.Controller):
    BASE_URL = '/api/employees'
    BASE_URL_LEAVE = '/api/leave'
    BASE_URLS = '/api'

    active_websockets = []

    @http.route(BASE_URL, auth='public', methods=['GET'], csrf=False)
    def index(self, **kw):
        return "Hello, world"

    @token_required
    @http.route(f"{BASE_URL}/<int:employee_id>", auth='public', methods=['GET'], csrf=False)
    def get_employee_by_id(self, employee_id):
        try:
            employee = request.env['hr.employee'].sudo().browse(employee_id)

            if not employee.exists():
                return werkzeug.wrappers.Response(
                    json.dumps({
                        "success": False,
                        "error": "Employee not found",
                        "status_code": 404,
                    }),
                    content_type='application/json',
                    status=404
                )

            response_data = {
                "success": True,
                "status_code": 200,
                "data": {
                    "employee_data": {
                        "id": employee.id,
                        "name": employee.name,
                        "email": employee.user_id.login if employee.user_id else "",
                        "work_phone": employee.work_phone,
                        "work_mobile": employee.mobile_phone,
                    },
                    "contract_details": {
                        "department": employee.department_id.name,

                        "job_position": employee.job_id.name if employee.job_id else "",
                        "first_contract_date": employee.first_contract_date.strftime(
                            '%Y-%m-%d') if employee.first_contract_date else "",
                        "contract": employee.contract_id.name if employee.contract_id else "",
                    },
                    "personal_documents": {
                        'bi': employee.identification_id,
                        'nuit': employee.x_nuit,
                    }
                }
            }

            return werkzeug.wrappers.Response(
                json.dumps(response_data),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "status_code": 500,
                }),
                content_type='application/json',
                status=500
            )

    # @token_required
    @http.route(f"{BASE_URL}/image/<int:employee_id>", type='http', auth='none', cors='*', csrf=False,
                methods=['GET'])
    def api_getimage_candidate(self, employee_id):

        if not employee_id:
            response_data = json.dumps(
                {
                    "success": False,
                    "error": "employee_id is required"
                }
            )
            return request.make_response(
                response_data,
                status=400,
                headers=[('Content-Type', 'application/json')]
            )

        employee = request.env['hr.employee'].sudo().search([('id', '=', int(employee_id))], limit=1)

        if not employee:
            response_data = json.dumps(
                {
                    "success": False,
                    "error": "employee_id not found"
                }
            )
            return request.make_response(
                response_data,
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        if employee.image_1920:
            image_data = base64.b64decode(employee.image_1920)
            headers = [
                ('Content-Type', 'image/jpeg'),
                ('Content-Length', str(len(image_data)))
            ]
            return request.make_response(image_data, headers=headers)

        response_data = json.dumps({"error": "No image found for this employee"})
        return request.make_response(
            response_data,
            headers=[('Content-Type', 'application/json')]
        )

    def strip_html_tags(self, html):
        import re
        clean = re.sub(r'<[^>]*?>', '', html)
        return clean.strip()

    @token_required
    @http.route(f"{BASE_URL}/announcements/<int:employee_id>", type='http', auth='none', cors='*', csrf=False,
                methods=['GET'])
    def get_announcements_by_department(self, employee_id):
        if not employee_id:
            response_data = json.dumps({"error": "employee_id is required"})
            return request.make_response(
                response_data,
                status=400,
                headers=[('Content-Type', 'application/json')]
            )

        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)

        if not employee:
            response_data = json.dumps({"error": "employee_id not found"})
            return werkzeug.wrappers.Response(
                response_data,
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        department_ids = employee.department_id.ids
        announcements = request.env['hr.announcement'].sudo().search([('department_ids', 'in', department_ids)])

        if not announcements:
            response_data = json.dumps({
                "success": False,
                "status_code": 404,
                "error": "No announcements found for this department"
            })
            return werkzeug.wrappers.Response(
                response_data,
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        announcements_data = []
        for announcement in announcements:
            plain_text = self.strip_html_tags(announcement.announcement)  # Agora funciona corretamente
            announcements_data.append({
                'id': announcement.id,
                'title': announcement.announcement_reason,
                'announcement': plain_text,
                'date_start': announcement.date_start.strftime('%Y-%m-%d'),
                'department': ', '.join([dept.name for dept in announcement.department_ids]),
            })

        return werkzeug.wrappers.Response(
            json.dumps({"announcements": announcements_data}),
            status=200,
            headers=[('Content-Type', 'application/json')]
        )

    @token_required
    @http.route(f"{BASE_URLS}/announcements/last/<int:employee_id>", type='http', auth='none', cors='*', csrf=False,
                methods=['GET'])
    def get_last_announcement_by_department(self, employee_id):
        if not employee_id:
            response_data = json.dumps({"error": "employee_id is required"})
            return request.make_response(
                response_data,
                status=400,
                headers=[('Content-Type', 'application/json')]
            )

        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)

        if not employee:
            response_data = json.dumps({"error": "employee_id not found"})
            return werkzeug.wrappers.Response(
                response_data,
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        department_ids = employee.department_id.ids
        announcement = request.env['hr.announcement'].sudo().search(
            [('department_ids', 'in', department_ids)],
            order='date_start desc',
            limit=1
        )

        if not announcement:
            response_data = json.dumps({
                "success": False,
                "status_code": 404,
                "error": "No announcements found for this department"
            })
            return werkzeug.wrappers.Response(
                response_data,
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        plain_text = self.strip_html_tags(announcement.announcement)

        announcement_data = {
            'id': announcement.id,
            'title': announcement.announcement_reason,
            'announcement': plain_text,
            'date_start': announcement.date_start.strftime('%Y-%m-%d'),
            'department': ', '.join([dept.name for dept in announcement.department_ids]),
        }

        return werkzeug.wrappers.Response(
            json.dumps({"last_announcement": announcement_data}),
            status=200,
            headers=[('Content-Type', 'application/json')]
        )

    @http.route(f'{BASE_URLS}/announcements/department/<int:employee_id>', type='http', auth='none', cors='*',
                csrf=False, methods=['GET'])
    def get_announcements(self, employee_id):

        info = []

        if not employee_id:
            return werkzeug.wrappers.Response(
                json.dumps(
                    {
                        "error": "employee_id is required",
                        "status_code": 400
                    }
                ),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        employee = request.env['hr.employee'].sudo().browse(employee_id)

        if not employee:
            return werkzeug.wrappers.Response(
                json.dumps(
                    {
                        "error": "employee_id not found",
                        "status_code": 404
                    }
                ), headers=[('Content-Type', 'application/json')],
                status=404
            )

        department_ids = employee.department_id.ids

        announcements = request.env['hr.announcement'].sudo().search([
            ('department_ids', 'in', department_ids),
        ])

        if not announcements:
            return werkzeug.wrappers.Response(
                json.dumps(
                    {"error": "No announcements found for this department"}
                ),
            )
        for announcement in announcements:
            info.append({
                'id': announcement.id,
                'title': announcement.announcement_reason,
                "state": announcement.state,
            })

        return werkzeug.wrappers.Response(
            json.dumps(
                {
                    "success": True,
                    "status": 200,
                    "data": info
                }
            ), headers=[('Content-Type', 'application/json')],
            status=200
        )

    @http.route(f'{BASE_URLS}/announcements/image/<int:announcements_id>', type='http', auth='none', cors='*',
                csrf=False, methods=['GET'])
    def get_announcements_image(self, announcements_id):
        if not announcements_id:
            print(announcements_id)
            return werkzeug.wrappers.Response(
                json.dumps(
                    {
                        'success': False,
                        'error': 'announcements_id is required',
                        'status_code': 400,

                    }
                ), headers=[('Content-Type', 'application/json')],
                status=400
            )
        announcement = request.env['hr.announcement'].sudo().search([('id', '=', int(announcements_id))], limit=1)

        if not announcement:
            response_data = json.dumps(
                {
                    "success": False,
                    "error": "announcement not found"
                }
            )
            return werkzeug.wrappers.Response(
                response_data,
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        if announcement.banner:
            image_data = base64.b64decode(announcement.banner)
            headers = [
                ('Content-Type', 'image/jpeg'),
                ('Content-Length', str(len(image_data)))
            ]
            return request.make_response(image_data, headers=headers)

        response_data = json.dumps({"error": "No image found for this announcement"})
        return request.make_response(
            response_data,
            headers=[('Content-Type', 'application/json')]
        )

    @token_required
    @http.route(f"{BASE_URL}/leave-types", type='http', auth='none', cors='*', csrf=False,
                methods=['GET'])
    def get_employee_leave_types(self):

        leave_types = request.env['hr.leave.type'].sudo().search([])

        leave_data = [{
            "id": leave.id,
            "name": leave.name,
        } for leave in leave_types]

        return werkzeug.wrappers.Response(
            json.dumps({"leave_types": leave_data}),
            status=200,
            headers=[('Content-Type', 'application/json')]
        )

    @token_required
    @http.route(f"{BASE_URL_LEAVE}/time-offs", type='json', auth='none', methods=['POST'], csrf=False)
    def create_time_off(self, **post):
        try:
            data = request.jsonrequest

            required_fields = ['employee_id', 'leave_type_id', 'date_from', 'date_to']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "status_code": 400,
                }

            maputo_tz = pytz.timezone('Africa/Maputo')
            utc_tz = pytz.utc

            try:
                naive_dt_from = datetime.strptime(data['date_from'], '%Y-%m-%d')
                dt_from = maputo_tz.localize(naive_dt_from)

                naive_dt_to = datetime.strptime(data['date_to'], '%Y-%m-%d')
                dt_to = maputo_tz.localize(naive_dt_to)
            except ValueError:
                return {
                    "success": False,
                    "error": "Invalid date format. Use 'YYYY-MM-DD'",
                    "status_code": 400,
                }

            if dt_to < dt_from:
                return {
                    "success": False,
                    "error": "End date must be greater than or equal to start date",
                    "status_code": 400,
                }

            employee = request.env['hr.employee'].sudo().browse(int(data['employee_id']))
            if not employee.exists():
                return {
                    "success": False,
                    "error": "Employee not found",
                    "status_code": 404,
                }

            leave_type = request.env['hr.leave.type'].sudo().browse(int(data['leave_type_id']))
            if not leave_type.exists():
                return {
                    "success": False,
                    "error": "Leave Type not found",
                    "status_code": 404,
                }

            existing_leaves = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', 'not in', ['cancel', 'refuse']),
                ('date_from', '<=', dt_to.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S')),
                ('date_to', '>=', dt_from.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S')),
            ])

            if existing_leaves:
                return {
                    "success": False,
                    "error": "Employee already has time off in this period",
                    "conflicting_leaves": [{
                        'id': leave.id,
                        'date_from': leave.date_from,
                        'date_to': leave.date_to,
                        'status': leave.state
                    } for leave in existing_leaves],
                    "status_code": 400,
                }

            # Get working hours for the employee
            work_schedule = self.work_days(employee.resource_calendar_id, day_ofweek=dt_from.weekday())
            if not work_schedule:
                return {
                    "success": False,
                    "error": "No working schedule found for this day",
                    "status_code": 400,
                }

            # Assume work_schedule returns periods ordered [morning, afternoon]
            morning_period = work_schedule[0]
            afternoon_period = work_schedule[1] if len(work_schedule) > 1 else morning_period

            # Combine dates with working hours
            request_date_from = maputo_tz.localize(datetime.combine(
                dt_from.date(),
                morning_period['hour_from']  # Hora de início do turno da manhã
            ))

            request_date_to = maputo_tz.localize(datetime.combine(
                dt_to.date(),
                afternoon_period['hour_to']  # Hora de término do turno da tarde
            ))

            # Prepare leave values with proper working hours
            leave_vals = {
                "employee_id": employee.id,
                'holiday_status_id': leave_type.id,
                "date_from": request_date_from.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S'),
                "date_to": request_date_to.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S'),
                'request_date_from': request_date_from.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S'),
                'request_date_to': request_date_to.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S'),
                "state": "confirm",
                "name": data.get("description", ""),
            }

            # Create the leave request
            try:
                with request.env.cr.savepoint():
                    leave = request.env['hr.leave'].sudo().create(leave_vals)
                    return {
                        "success": True,
                        "message": "Time off created successfully",
                        "leave_id": leave.id,
                        "status_code": 201,
                    }
            except Exception as create_error:
                return {
                    "success": False,
                    "error": str(create_error),
                    "status_code": 400,
                }

        except Exception as e:
            return {
                "success": False,
                "error": "Internal server error",
                "status_code": 500,
            }

    @http.route(f'{BASE_URL_LEAVE}/<int:employee_id>', type='http', auth='none', methods=['GET'])
    def get_leave(self, employee_id):
        info = []
        if not employee_id:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'success': False,
                    'error': 'Employee is required.',
                    'status_code': 400,
                }), headers={'Content-Type': 'application/json'},
                status=400
            )

        employee = request.env['hr.employee'].sudo().browse(employee_id)
        if not employee.exists():
            return werkzeug.wrappers.Response(
                json.dumps({
                    'success': False,
                    'error': 'Employee not found.',
                    'status_code': 404,
                }), headers={'Content-Type': 'application/json'},
                status=404
            )

        leaves = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id),
        ])

        for leave in leaves:
            info.append({
                'employee_id': {
                    'id': leave.employee_id.id,
                    'name': leave.employee_id.name
                },
                'leave_type': {
                    'id': leave.holiday_status_id.id,
                    'name': leave.holiday_status_id.name
                },
                'date_from': leave.date_from.strftime('%Y-%m-%d') if leave.date_from else None,
                'date_to': leave.date_to.strftime('%Y-%m-%d') if leave.date_to else None,
                'request_date_from': leave.request_date_from.strftime('%Y-%m-%d') if leave.request_date_from else None,
                'request_date_to': leave.request_date_to.strftime('%Y-%m-%d') if leave.request_date_to else None,
                'state': leave.state,
                'name': leave.name,
                'description': leave.name
            })

        return werkzeug.wrappers.Response(
            json.dumps({
                'success': True,
                'status': 200,
                'data': info,
            }), headers={'Content-Type': 'application/json'},
            status=200
        )

    def work_days(self, resource_calendar, day_ofweek):

        if not resource_calendar:
            return []

        attendances = resource_calendar.attendance_ids.filtered(
            lambda a: int(a.dayofweek) == day_ofweek
        )

        work_schedule = []
        for attendance in attendances:
            try:
                hour_from = time(
                    int(attendance.hour_from),
                    int((attendance.hour_from % 1) * 60)
                )
                hour_to = time(
                    int(attendance.hour_to),
                    int((attendance.hour_to % 1) * 60)
                )

                work_schedule.append({
                    'hour_from': hour_from,
                    'hour_to': hour_to,
                })
            except ValueError as e:
                raise ValueError(f"Erro ao processar horários: {e}")

        return work_schedule

    @token_required
    @http.route(f"{BASE_URLS}/loan", type='json', auth='none', methods=['POST'], csrf=False)
    def create_loan(self):

        data = request.jsonrequest

        print(data)

        required_fields = ['employee_id', 'amount', 'payment_date', 'installment']
        if not all(field in data for field in required_fields):
            return {
                "success": False,
                "error": "Required fields are missing",
                "status_code": 400,
            }

        employee_id = data['employee_id']
        loan_amount = data['amount']
        payment_date = data['payment_date']
        installment = data['installment']

        data = datetime.today().strftime('%Y-%m-%d')

        employee = request.env['hr.employee'].sudo().browse(employee_id)
        if not employee.exists():
            return {
                "success": False,
                "error": "Employee not found",
                "status_code": 404,
            }

        contract = request.env['hr.contract'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'open')
        ], limit=1)

        company_id = employee.company_id.id if employee.company_id else None
        department_id = employee.department_id.id if employee.department_id else None
        job_position_id = employee.job_id.id if employee.job_id else None

        currency_id = contract.currency_id.id if contract else employee.company_id.currency_id.id if employee.company_id else None

        print(job_position_id)

        loan = request.env['hr.loan'].sudo().create({
            'name': '/',
            'employee_id': employee.id,
            'date': data,
            'loan_amount': loan_amount,
            'payment_date': payment_date,
            'currency_id': currency_id,
            'installment': installment,
            'company_id': company_id,
            'department_id': department_id,
            'job_position': job_position_id,
            'state': 'waiting_approval_1',
        })

        return {
            "success": True,
            "message": "Loan created successfully",
            "status_code": 201,
        }

    @token_required
    @http.route([f"{BASE_URLS}/loan/<int:employee_id>"], type='http', auth='none', methods=['GET'], csrf=False)
    def get_loan(self, employee_id):

        data = []
        if not employee_id:
            return werkzeug.wrappers.Response(
                json.dumps({'success': False,
                            'error': 'Employee is required'}),
                headers={'Content-Type': 'application/json'},
                status=400)

        employee = request.env['hr.employee'].sudo().browse(employee_id)

        if not employee.exists():
            return werkzeug.wrappers.Response(
                json.dumps(
                    {
                        'success': False,
                        'error': 'Employee not found',
                        'status_code': 404,
                    }
                ),
                headers={'Content-Type': 'application/json'},
                status=404
            )
        loan = request.env['hr.loan'].sudo().search([
            ('employee_id', '=', employee.id),
        ])

        for loan in loan:
            data.append({
                'employee_id': employee.id,
                'loan_amount': loan.loan_amount,
                'installment': loan.installment,
                'department_id': employee.department_id.name,
                'job_position': employee.job_id.name,
                'payment_date': loan.payment_date.strftime('%Y-%m-%d'),
                'date': loan.date.strftime('%Y-%m-%d'),
                'state': loan.state,
            })

        return werkzeug.wrappers.Response(
            json.dumps(
                {
                    'success': True,
                    "status_code": 200,
                    "data": data,
                }
            ), headers={'Content-Type': 'application/json'},
            status=200,
        )

    @token_required
    @http.route(f"{BASE_URLS}/currencies", type='http', auth='none', methods=['GET'], csrf=False)
    def get_currencies(self):

        currencies = request.env['res.currency'].search([])

        info = []

        for currency in currencies:
            info.append({
                'id': currency.id,
                'name': currency.name,
                "symbol": currency.symbol,
                "code": currency.currency_unit_label
            })

        return werkzeug.wrappers.Response(json.dumps(
            {
                "success": True,
                "data": info,
                "status_code": 200,
            },

        ), headers={'Content-Type': 'application/json'}, status=200)

    # @token_required
    @http.route(f"{BASE_URL}/calendar/<int:employee_id>", type='http', auth='none', methods=['GET'])
    def get_employee_calendar(self, employee_id):

        employee = request.env['hr.employee'].sudo().browse(employee_id)

        if not employee.exists():
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "Employee not found",
                    "status_code": 404,
                }),
                content_type='application/json',
                status=404
            )

        employee.invalidate_cache(['resource_calendar_id'])
        resource_calendar = employee.resource_calendar_id

        if not resource_calendar:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "Employee resource calendar not found",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        today = datetime.today()
        year = today.year
        month = today.month

        num_days = calendar.monthrange(year, month)[1]
        all_days = [datetime(year, month, day) for day in range(1, num_days + 1)]

        off_days = []
        working_days = []

        for day in all_days:
            weekday = day.weekday()

            working_intervals = resource_calendar.attendance_ids.filtered(
                lambda att: int(att.dayofweek) == weekday
            )

            if not working_intervals:
                off_days.append(day.strftime('%d'))
            else:
                working_days.append(day.strftime('%d'))

        return werkzeug.wrappers.Response(
            json.dumps({
                "success": True,
                "status_code": 200,
                "data": {
                    "employee_name": employee.name,
                    "month": month,
                    "year": year,
                    "working_days": working_days,
                    "off_days": off_days,
                }
            }),
            headers={'Content-Type': 'application/json'},
            status=200
        )

    @token_required
    @http.route(f"{BASE_URL}/working-hours/<int:employee_id>", type='http', auth='none', methods=['GET'])
    def get_working_hours_for_today(self, employee_id):
        employee = request.env['hr.employee'].sudo().browse(employee_id)

        if not employee.exists():
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "Employee not found",
                    "status_code": 404,
                }),
                content_type='application/json',
                status=404
            )

        resource_calendar = employee.resource_calendar_id
        if not resource_calendar:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "Employee resource calendar not found",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        today = datetime.today()
        weekday = today.weekday()

        working_intervals = resource_calendar.attendance_ids.filtered(
            lambda att: int(att.dayofweek) == weekday
        ).sorted(key=lambda x: x.hour_from)

        if not working_intervals:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"No working hours found for {today.strftime('%Y-%m-%d')}",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        working_hours = {
            'morning': [],
            'afternoon': []
        }

        for interval in working_intervals:
            period_data = {
                "start": interval.hour_from,
                "end": interval.hour_to,
            }

            if interval.day_period == 'morning':
                working_hours['morning'].append(period_data)
            elif interval.day_period == 'afternoon':
                working_hours['afternoon'].append(period_data)

        return werkzeug.wrappers.Response(
            json.dumps({
                "success": True,
                "status_code": 200,
                "data": {
                    "employee_name": employee.name,
                    "date": today.strftime('%Y-%m-%d'),
                    "working_hours": working_hours,

                }
            }),
            headers={'Content-Type': 'application/json'},
            status=200
        )

    @http.route(f"{BASE_URL}/attendance/<int:employee_id>", type='http', auth='none', methods=['GET'])
    def get_attendance(self, employee_id, **kwargs):
        date_from = kwargs.get('date_from')
        date_to = kwargs.get('date_to')
        limit = int(kwargs.get('limit', 10))
        offset = int(kwargs.get('offset', 0))
        tz_maputo = pytz.timezone('Africa/Maputo')

        if not date_from or not date_to:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"No date from {date_from} to {date_to}",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )
        if date_from > date_to:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": 'date_from cannot be greater than date_to',
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)
        if not employee:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"Employee {employee_id} not found",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', date_from),
            ('check_in', '<=', date_to)
        ], limit=limit, offset=offset)

        attendance_data = []
        for att in attendances:
            check_in_local = att.check_in.astimezone(tz_maputo) if att.check_in else None
            check_out_local = att.check_out.astimezone(tz_maputo) if att.check_out else None

            attendance_data.append({
                'check_in': check_in_local.strftime('%Y-%m-%d') if check_in_local else "",
                'hora_check_in': check_in_local.strftime('%H:%M') if check_in_local else "",
                'check_out': check_out_local.strftime('%Y-%m-%d') if check_out_local else "",
                'hora_check_out': check_out_local.strftime('%H:%M') if check_out_local else "",
            })

        total_attendances = request.env['hr.attendance'].sudo().search_count([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', date_from),
            ('check_in', '<=', date_to)
        ])

        leaves = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee_id),
            ('request_date_from', '>=', date_from),
            ('request_date_to', '<=', date_to)
        ], limit=limit, offset=offset)

        leave_data = [{
            'holiday_status': leave.holiday_status_id.name,
            'request_date_from': leave.request_date_from.strftime('%Y-%m-%d ') if leave.request_date_from else "",
            'request_date_to': leave.request_date_to.strftime('%Y-%m-%d ') if leave.request_date_to else "",
            'state': leave.state
        } for leave in leaves]

        total_leaves = request.env['hr.leave'].sudo().search_count([
            ('employee_id', '=', employee_id),
            ('request_date_from', '>=', date_from),
            ('request_date_to', '<=', date_to)
        ])

        total_dias = total_attendances + total_leaves
        if total_dias > 0:
            attendance_percentage = (total_attendances / total_dias) * 100
            leaves_percentage = (total_leaves / total_dias) * 100
        else:
            attendance_percentage = 0.0
            leaves_percentage = 0.0

        return werkzeug.wrappers.Response(
            json.dumps({
                'employee_id': employee.id,
                'employee_name': employee.name,
                'attendance': attendance_data,
                'total_attendance': total_attendances,
                'leaves': leave_data,
                'total_leaves': total_leaves,
                'attendance_percentage': round(attendance_percentage, 2),
                'leaves_percentage': round(leaves_percentage, 2),
                'limit': limit,
                'offset': offset
            }),
            headers={'Content-Type': 'application/json'},
            status=200
        )

    # @token_required
    @http.route(f"{BASE_URL}/payslips/<int:employee_id>/", type='http', auth='none', methods=['GET'])
    def get_payslips(self, employee_id, **kwargs):

        payslip_month = kwargs.get('month')
        current_year = kwargs.get('year')

        try:
            if payslip_month:
                payslip_month = int(payslip_month)
            else:
                raise ValueError("month is required")

            if current_year:
                current_year = int(current_year)
            else:
                raise ValueError("year is required")
        except ValueError as e:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "status_code": 400,
                }),
                headers={'Content-Type': 'application/json'},
                status=400
            )

        if payslip_month < 1 or payslip_month > 12:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "Month must be between 1 and 12",
                    "status_code": 400,
                }),
                headers={'Content-Type': 'application/json'},
                status=400
            )

        try:
            if payslip_month == 12:
                last_day = 31
            else:
                last_day = (datetime(current_year, payslip_month + 1, 1) - timedelta(days=1)).day

            date_from = f'{current_year}-{payslip_month:02d}-01'
            date_to = f'{current_year}-{payslip_month:02d}-{last_day:02d}'
        except ValueError as e:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "status_code": 400,
                }),
                headers={'Content-Type': 'application/json'},
                status=400
            )

        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)
        if not employee:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"Employee {employee_id} not found",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        payslips = request.env['hr.payslip'].sudo().search([
            ('employee_id', '=', employee_id),
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to)
        ])

        if not payslips:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"No payslips found for employee {employee.name}",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        company = employee.company_id
        employee_data = {
            'id': company.id,
            "employee_name": employee.name,
            "employee_id": employee.id,
            "job_position": employee.job_id.name,
            'company_details': company.company_details,
            'company_id': company.id,
            'company_name': company.name,

            'street': company.street,
            'vat': company.vat

        }

        payslip_data = [{
            'name': payslip.name,
            'create_date': payslips.create_date.strftime('%m-%d-%Y'),
            'date_from': payslip.date_from.strftime('%Y-%m-%d') if payslip.date_from else None,
            'date_to': payslip.date_to.strftime('%Y-%m-%d') if payslip.date_to else None,
            "reference": payslip.number,
            "contract": payslip.contract_id.name,
            "structure": payslip.struct_id.name,
            "WorkedDays": [{
                "description": wd.name,
                "code": wd.code,
                "number_of_days": wd.number_of_days,
            } for wd in payslip.worked_days_line_ids],

            # "details_by_salary_rule_category": [{
            #     "category_id": dc.category_id.name,
            #     "name": dc.name,
            #     "code": dc.code,
            #     "total": dc.total,
            # } for dc in payslip.details_by_salary_rule_category],

            # "line_ids": [{
            #     "name": ld.name,
            #     "code": ld.code,
            #     "category_id": ld.category_id.name,
            #     "quantity": ld.quantity,
            #     "amount": ld.amount,
            #     "total": ld.total,
            # } for ld in payslips.line_ids],

            # Dentro do loop que gera payslip_data, substitua a parte de input_line_ids por:

            "input_line_ids": {
                "earnings": {
                    "items": [
                                 {
                                     "name": inp.name,
                                     "code": inp.code,
                                     "amount": inp.amount
                                 } for inp in payslip.input_line_ids if inp.code in ['H_E_150', 'H_E_200']
                             ] + [{
                        "name": "Basic Salary",
                        "code": "BASIC",
                        "amount": next((line['total'] for line in payslip.line_ids if line['code'] == 'BASIC'), 0.0)
                    }],
                    "total": sum(inp.amount for inp in payslip.input_line_ids if inp.code in ['H_E_150', 'H_E_200']) +
                             next((line['total'] for line in payslip.line_ids if line['code'] == 'BASIC'), 0.0)
                },
                "deductions": {
                    "items": [
                                 {
                                     "name": inp.name,
                                     "code": inp.code,
                                     "amount": abs(inp.amount)
                                 } for inp in payslip.input_line_ids if inp.code in ['D_P_A', 'DFF', 'DD']
                             ] + [{
                        "name": "INSS",
                        "code": "INSS",
                        "amount": abs(next((line['total'] for line in payslip.line_ids if line['code'] == 'INSS'), 0.0))
                    }],
                    "total": sum(
                        abs(inp.amount) for inp in payslip.input_line_ids if inp.code in ['D_P_A', 'DFF', 'DD']) +
                             abs(next((line['total'] for line in payslip.line_ids if line['code'] == 'INSS'), 0.0))
                },
                "net_total": (sum(inp.amount for inp in payslip.input_line_ids if inp.code in ['H_E_150', 'H_E_200']) +
                              next((line['total'] for line in payslip.line_ids if line['code'] == 'BASIC'), 0.0)) -
                             (sum(abs(inp.amount) for inp in payslip.input_line_ids if
                                  inp.code in ['D_P_A', 'DFF', 'DD']) +
                              abs(next((line['total'] for line in payslip.line_ids if line['code'] == 'INSS'), 0.0)))
            }
        } for payslip in payslips]

        return werkzeug.wrappers.Response(
            json.dumps({
                "success": True,
                "status_code": 200,
                "data": {
                    "employee_data": employee_data,
                    "payslips": payslip_data,

                }
            }),
            headers={'Content-Type': 'application/json'},
            status=200
        )

    @token_required
    @http.route(f"{BASE_URL}/<int:employee_id>/payslips/pdf", type='http', auth='none', methods=['GET'])
    def get_payslips_pdf(self, employee_id, **kwargs):
        payslip_month = kwargs.get('month')
        current_year = datetime.now().year

        if not payslip_month:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "month is required",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)
        if not employee:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"Employee {employee_id} not found",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        payslips = request.env['hr.payslip'].sudo().search([
            ('employee_id', '=', employee_id),
            ('date_from', '>=', f'{current_year}-{payslip_month}-01'),
            ('date_to', '<=', f'{current_year}-{payslip_month}-31')
        ])

        if not payslips:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"No payslips found for employee {employee.name} ",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        pdf_buffer = io.BytesIO()
        p = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 16)
        p.drawString(200, height - 50, "Payslip Report")

        p.setFont("Helvetica", 12)
        p.drawString(50, height - 80, f"Employee: {employee.name}")
        p.drawString(50, height - 100, f"Month: {payslip_month}/{current_year}")

        y_position = height - 130

        for payslip in payslips:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y_position, f"Payslip: {payslip.name}")
            y_position -= 20

            p.setFont("Helvetica", 10)
            p.drawString(50, y_position,
                         f"Date From: {payslip.date_from.strftime('%Y-%m-%d') if payslip.date_from else ''}")
            p.drawString(250, y_position, f"Date To: {payslip.date_to.strftime('%Y-%m-%d') if payslip.date_to else ''}")
            y_position -= 20

            if y_position < 100:
                p.showPage()
                y_position = height - 50

        p.showPage()
        p.save()

        pdf_buffer.seek(0)

        return werkzeug.wrappers.Response(
            pdf_buffer.read(),
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename=payslip_{employee_id}_{payslip_month}.pdf')
            ],
            status=200
        )

    @token_required
    @http.route(f"{BASE_URL}/overtime/<int:employee_id>/", type='http', auth='none', methods=['GET'])
    def get_overtime(self, employee_id, **kwargs):
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        info = []

        if not start_date or not end_date:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "start_date and end_date are required",
                    "status_code": 400,
                }),
                headers={'Content-Type': 'application/json'},
                status=400
            )

        if start_date > end_date:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "Start date cannot be greater than end date",
                    "status_code": 400,
                }),
                headers={'Content-Type': 'application/json'},
                status=400
            )

        employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)
        if not employee:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"Employee {employee_id} not found",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        overtime_records = request.env['hr.attendance.overtime'].sudo().search([
            ('employee_id', '=', employee_id),
            ("date", ">=", start_date),
            ("date", "<=", end_date),
        ])

        if not overtime_records:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"No overtime records found for employee {employee.name}",
                    "status_code": 404,
                    "employee_id": employee.id,
                    "employee_name": employee.name,
                    "period": f"{start_date} to {end_date}"
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        for overtime_record in overtime_records:
            total_hours = abs(overtime_record.duration)
            hours = int(total_hours)
            minutes = int((total_hours - hours) * 60)
            formatted_duration = f"{'-' if overtime_record.duration < 0 else ''}{hours:02d}:{minutes:02d}"

            info.append({
                'employee_id': employee_id,
                'employee_name': employee.name,
                'date': overtime_record.date.strftime('%Y-%m-%d'),
                'duration': formatted_duration,

            })

        return werkzeug.wrappers.Response(
            json.dumps({
                "success": True,
                "status_code": 200,
                "data": info,
            }),
            headers={'Content-Type': 'application/json'},
            status=200
        )

    @token_required
    @http.route(f"{BASE_URLS}/certification", type='json', auth='none', methods=['POST'])
    def create_certification(self):
        data = request.jsonrequest

        employee_id = data.get('employee_id')
        certificate_type = data.get('certificate_type')
        request_date = datetime.today()

        if not certificate_type or not employee_id:
            return {
                "success": False,
                "error": "certificate_type and employee_id are required",
                "status_code": 404,
            }

        employee = request.env['hr.employee'].sudo().browse(employee_id)
        if not employee.exists():
            return {
                "success": False,
                "error": f"Employee {employee_id} not found",
                "status_code": 404,
            }

        certificate = request.env['certificate.request'].sudo().create({
            'employee_id': employee_id,
            'certificatetype': certificate_type,
            'state': 'requested',
            'request_date': request_date,
            'department_id': employee.department_id.id,
        })

        return {
            "success": True,
            "status_code": 201,
            "message": "Certificate request created successfully",
            "certificate_id": certificate.id
        }

    @token_required
    @http.route([f"{BASE_URLS}/certification/<int:id>"], type='http', auth='none', methods=['GET'])
    def get_certificate_request(self, id):
        info = []
        if not id:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "employee_id are required",
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        employee = request.env['hr.employee'].sudo().browse(id)
        if not employee.exists():
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "Employee not found",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        certificate = request.env['certificate.request'].sudo().search([
            ('employee_id', '=', id)
        ])

        if not certificate:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "No request found for this employee.",
                    "status_code": 404,
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        for certificates in certificate:
            info.append({
                'id': certificates.id,
                'employee_id': employee.id,
                'certificate_type': certificates.certificatetype,
                'state': certificates.state,
                'request_date': certificates.request_date.strftime('%Y-%m-%d'),
                'department_id': certificates.department_id.id,
                'notes': certificates.notes if certificates.notes else "",

            })

        return werkzeug.wrappers.Response(
            json.dumps({
                "success": True,
                "status_code": 200,
                "data": info,
            }),
            headers={'Content-Type': 'application/json'},
            status=200
        )

    @token_required
    @http.route(f'{BASE_URLS}/certification/check/<int:certificate_id>', type='http', auth='none', methods=['GET'],
                csrf=False)
    def check_certificate_attachment(self, certificate_id):

        certificate = request.env['certificate.request'].sudo().browse(certificate_id)

        if not certificate.exists():
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "message": "Certificate request not found."
                }), content_type="application/json", status=404
            )

        has_attachments = bool(certificate.supported_attachment_ids)

        return werkzeug.wrappers.Response(
            json.dumps({
                "success": True,
                "has_attachments": has_attachments
            }), content_type="application/json", status=200
        )

    @token_required
    @http.route(f'{BASE_URLS}/certification/download/<int:certificate_id>', type='http', auth='none', methods=['GET'])
    def download_certificate_attachments(self, certificate_id):
        certificate = request.env['certificate.request'].sudo().browse(certificate_id)

        if not certificate or not certificate.supported_attachment_ids:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "No attachments found for this certificate request."
                }), content_type="application/json", status=404
            )

        attachment = certificate.supported_attachment_ids[0]
        file_content = base64.b64decode(attachment.datas)
        file_name = attachment.name

        response = werkzeug.wrappers.Response(file_content, content_type=attachment.mimetype)
        response.headers.add('Content-Disposition', f'attachment; filename="{file_name}"')
        return response

    @http.route(f'{BASE_URLS}/shift/create', type='json', auth='none', methods=['POST'])
    def create_shift_swap(self, **post):
        try:
            data = request.jsonrequest

            required_fields = ['employee_id', 'requested_employee_id', 'date_from', 'date_to', 'day_period']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}',
                    'status_code': 400
                }

            employee = request.env['hr.employee'].sudo().browse(int(data['employee_id']))
            requested_employee = request.env['hr.employee'].sudo().browse(int(data['requested_employee_id']))

            if employee.department_id != requested_employee.department_id:
                return {
                    'success': False,
                    'error': 'Só é permitido trocar turnos com pessoas do mesmo departamento',
                    'status_code': 403
                }

            swap = request.env['shift.swap'].sudo().create({
                'employee_id': data['employee_id'],
                'requested_employee_id': data['requested_employee_id'],
                'date_from': data['date_from'],
                'date_to': data['date_to'],
                'day_period': data['day_period'],
                'reason': data.get('reason', ''),
                'state': 'draft'
            })

            return {
                'success': True,
                'swap_id': swap.id,
                'message': 'Pedido de troca criado com sucesso',
                'status_code': 201
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }

    @http.route(f'{BASE_URLS}/shift/<int:employees_id>', type='http', auth='none', methods=['GET'])
    def get_shift(self, employees_id):
        try:
            if not employees_id:
                return werkzeug.wrappers.Response(
                    json.dumps({
                        "success": False,
                        "error": "Employee id is required.",
                        "status_code": 400
                    }),
                    content_type="application/json",
                    status=400
                )

            shift = request.env['shift.swap'].sudo().search([('employee_id', '=', employees_id)], limit=1)

            if not shift:
                return werkzeug.wrappers.Response(
                    json.dumps({
                        "success": False,
                        "error": "Shift not found",
                        "status_code": 404
                    }),
                    content_type="application/json",
                    status=404
                )

            info = {
                'employee_id': shift.employee_id.id if shift.employee_id else None,
                'employee_name': shift.employee_id.name if shift.employee_id else '',
                'requested_employee_id': shift.requested_employee_id.id if shift.requested_employee_id else None,
                'requested_employee_name': shift.requested_employee_id.name if shift.requested_employee_id else '',
                'date_from': shift.date_from.strftime('%Y-%m-%d') if shift.date_from else '',
                'date_to': shift.date_to.strftime('%Y-%m-%d') if shift.date_to else '',
                'day_period': shift.day_period,
                'reason': shift.reason or '',
                'state': shift.state,
            }

            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": True,
                    "status_code": 200,
                    "shift": info,
                }),
                content_type="application/json",
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "status_code": 500
                }),
                content_type="application/json",
                status=500
            )

    @http.route(f'{BASE_URLS}/shift/employees/<int:employee_id>', type='http', auth='none', methods=['GET'])
    def get_employees_by_department(self, employee_id, **kwargs):
        try:
            employee = request.env['hr.employee'].sudo().browse(employee_id)

            if not employee.exists():
                return werkzeug.wrappers.Response(
                    json.dumps({
                        "success": False,
                        "error": f"Funcionário com ID {employee_id} não encontrado",
                        "status_code": 404
                    }), headers={'Content-Type': 'application/json'},
                    status=404
                )

            if not employee.department_id:
                return werkzeug.wrappers.Response(
                    json.dumps({
                        "success": False,
                        "error": "Funcionário não está associado a um departamento",
                        "status_code": 400
                    }), headers={'Content-Type': 'application/json'},
                    status=400
                )

            employees = request.env['hr.employee'].sudo().search([
                ('department_id', '=', employee.department_id.id),
                ('id', '!=', employee.id)
            ])

            employees_data = [{
                'id': emp.id,
                'name': emp.name,
                'department': emp.department_id.name if emp.department_id else '',
                'current_shift': emp.resource_calendar_id.name if emp.resource_calendar_id else ''
            } for emp in employees]

            return werkzeug.wrappers.Response(
                json.dumps({
                    'success': True,
                    'department': employee.department_id.name,
                    'employees': employees_data,
                    'status_code': 200
                }), headers={'Content-Type': 'application/json'},
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                    'status_code': 500
                }), headers={'Content-Type': 'application/json'},
                status=500
            )

    @http.route(f'{BASE_URLS}/discuss/file/send', auth='none', cors='*', type='http', methods=['POST'], csrf=False)
    def discuss_send_file(self, **kwargs):
        try:
            if request.httprequest.content_type.startswith('multipart/form-data'):
                sender_id = request.params.get('sender_id')
                receiver_id = request.params.get('receiver_id')
                body = request.params.get('body')
                attachments = request.httprequest.files.getlist('attachments')
            else:
                data = json.loads(request.httprequest.data)
                sender_id = data.get('sender_id')
                receiver_id = data.get('receiver_id')
                body = data.get('body')
                attachments = []

            if not sender_id or not receiver_id:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'All fields are required',
                        'status_code': 400,
                    }),
                    content_type='application/json',
                    status=400
                )

            sender_employee = request.env['hr.employee'].sudo().browse(int(sender_id))
            receiver_employee = request.env['hr.employee'].sudo().browse(int(receiver_id))

            if not sender_employee.exists() or not receiver_employee.exists():
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Sender or Receiver not found',
                        'status_code': 404,
                    }),
                    content_type='application/json',
                    status=404
                )

            sender_user = sender_employee.sudo().user_id
            receiver_user = receiver_employee.sudo().user_id

            if not sender_user or not receiver_user:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Employees must have associated users',
                        'status_code': 400,
                    }),
                    content_type='application/json',
                    status=400
                )

            sender_partner = sender_user.partner_id
            receiver_partner = receiver_user.partner_id

            if not sender_partner or not receiver_partner:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Users must have associated partners',
                        'status_code': 400,
                    }),
                    content_type='application/json',
                    status=400
                )

            record_name = f"{receiver_user.name}, {sender_user.name}"

            attachment_ids = []
            for attachment in attachments:
                attachment_data = attachment.read()
                attachment_obj = request.env['ir.attachment'].sudo().create({
                    'name': attachment.filename,
                    'datas': base64.b64encode(attachment_data),
                    'res_model': 'mail.message',
                    'res_id': 0,
                    'type': 'binary',
                })
                attachment_ids.append(attachment_obj.id)

            message = request.env['mail.message'].sudo().with_context(no_name_get=True).create({
                'message_type': 'comment',
                'res_id': 6,
                'subtype_id': 1,
                'model': 'mail.channel',
                'reply_to': f'"{sender_user.name}" <{sender_user.login}>',
                'create_uid': sender_user.id,
                'author_id': sender_partner.id,
                'partner_ids': [(4, receiver_partner.id)],
                'record_name': record_name,
                'attachment_ids': [(6, 0, attachment_ids)] if attachment_ids else False,
            })

            if attachment_ids:
                request.env['ir.attachment'].sudo().browse(attachment_ids).write({
                    'res_id': message.id
                })

            print(f"Controller: Mensagem criada com ID {message.id}, enviando para WebSockets...")

            return Response(
                json.dumps({
                    'success': True,
                    'message_id': message.id,
                    'record_name': record_name,
                    'attachment_ids': attachment_ids,
                    'status_code': 201,
                }),
                content_type='application/json',
                status=201
            )

        except Exception as e:
            return Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                    'status_code': 500,
                }),
                content_type='application/json',
                status=500
            )

    @http.route(f'{BASE_URLS}/discuss/audio/send', auth='none', cors='*', type='http', methods=['POST'], csrf=False)
    def discuss_send_audio(self, **kwargs):
        try:
            if request.httprequest.content_type.startswith('multipart/form-data'):
                sender_id = request.params.get('sender_id')
                receiver_id = request.params.get('receiver_id')
                audio_file = request.httprequest.files.get('audio')
            else:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Only multipart/form-data is supported for audio',
                        'status_code': 400
                    }),
                    content_type='application/json',
                    status=400
                )

            if not sender_id or not receiver_id or not audio_file:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'sender_id, receiver_id and audio file are required',
                        'status_code': 400,
                    }),
                    content_type='application/json',
                    status=400
                )

            sender_employee = request.env['hr.employee'].sudo().browse(int(sender_id))
            receiver_employee = request.env['hr.employee'].sudo().browse(int(receiver_id))

            if not sender_employee.exists() or not receiver_employee.exists():
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Sender or Receiver not found',
                        'status_code': 404,
                    }),
                    content_type='application/json',
                    status=404
                )

            sender_user = sender_employee.sudo().user_id
            receiver_user = receiver_employee.sudo().user_id

            if not sender_user or not receiver_user:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Employees must have associated users',
                        'status_code': 400,
                    }),
                    content_type='application/json',
                    status=400
                )

            sender_partner = sender_user.partner_id
            receiver_partner = receiver_user.partner_id

            if not sender_partner or not receiver_partner:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Users must have associated partners',
                        'status_code': 400,
                    }),
                    content_type='application/json',
                    status=400
                )

            record_name = f"{receiver_user.name}, {sender_user.name}"

            # Conversão do áudio
            original_data = audio_file.read()
            original_ext = audio_file.filename.split('.')[-1].lower()
            audio = AudioSegment.from_file(io.BytesIO(original_data), format=original_ext)
            mp3_buffer = io.BytesIO()
            audio.export(mp3_buffer, format='mp3')
            mp3_data = mp3_buffer.getvalue()

            # Criação do attachment MP3
            attachment = request.env['ir.attachment'].sudo().create({
                'name': 'voice_message.mp3',
                'datas': base64.b64encode(mp3_data),
                'res_model': 'mail.message',
                'res_id': 0,
                'type': 'binary',
                'mimetype': 'audio/mpeg',
            })

            message = request.env['mail.message'].sudo().with_context(no_name_get=True).create({
                'message_type': 'comment',
                'res_id': 6,
                'subtype_id': 1,
                'model': 'mail.channel',
                'reply_to': f'"{sender_user.name}" <{sender_user.login}>',
                'create_uid': sender_user.id,
                'author_id': sender_partner.id,
                'partner_ids': [(4, receiver_partner.id)],
                'record_name': record_name,
                'attachment_ids': [(6, 0, [attachment.id])]
            })

            attachment.write({'res_id': message.id})

            print(f"[AUDIO CONTROLLER] Mensagem criada com ID {message.id}, attachment mp3 gerado.")

            return Response(
                json.dumps({
                    'success': True,
                    'message_id': message.id,
                    'record_name': record_name,
                    'attachment_id': attachment.id,
                    # 'url': f"/web/content/{attachment.id}?download=true",
                    'status_code': 201,
                }),
                content_type='application/json',
                status=201
            )

        except Exception as e:
            return Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                    'status_code': 500
                }),
                content_type='application/json',
                status=500
            )

    @http.route(f'{BASE_URLS}/users', csrf=False, auth='none', type='http', methods=['POST'])
    def users(self):
        users = request.env['res.users'].sudo().search([])
        info = []

        for none in users:
            info.append({
                'user_id': none.id,
                'name': none.name,
            })
        return werkzeug.wrappers.Response(
            json.dumps({
                'success': True,
                'users': info,
            }), headers={'Content-Type': 'application/json'},
            status=200
        )

    @http.route(f'{BASE_URLS}/discuss/send', auth='none', cors='*', type='json', methods=['POST'], csrf=False)
    def discuss_send(self, **kwargs):
        try:

            data = request.jsonrequest

            sender_id = data.get('sender_id')
            receiver_id = data.get('receiver_id')
            body = data.get('body')

            if not sender_id or not receiver_id or not body:
                return {
                    'success': False,
                    'error': 'All fields are required',
                    'status_code': 400,
                }

            sender_employee = request.env['hr.employee'].sudo().browse(int(sender_id))
            receiver_employee = request.env['hr.employee'].sudo().browse(int(receiver_id))

            if not sender_employee.exists() or not receiver_employee.exists():
                return {
                    'success': False,
                    'error': 'Sender or Receiver not found',
                    'status_code': 404,
                }

            sender_user = sender_employee.sudo().user_id
            receiver_user = receiver_employee.sudo().user_id

            if not sender_user or not receiver_user:
                return {
                    'success': False,
                    'error': 'Employees must have associated users',
                    'status_code': 400,
                }

            sender_partner = sender_user.partner_id
            receiver_partner = receiver_user.partner_id

            if not sender_partner or not receiver_partner:
                return {
                    'success': False,
                    'error': 'Users must have associated partners',
                    'status_code': 400,
                }

            record_name = f"{receiver_user.name}, {sender_user.name}"

            message = request.env['mail.message'].sudo().with_context(no_name_get=True).create({
                'message_type': 'comment',
                'body': body,
                'res_id': 6,
                'subtype_id': 1,
                'model': 'mail.channel',
                'reply_to': f'"{sender_user.name}" <{sender_user.login}>',
                'create_uid': sender_user.id,
                'author_id': sender_partner.id,
                'partner_ids': [(4, receiver_partner.id)],
                'record_name': record_name,

            })

            self.send_to_relevant_websockets(body, sender_id, receiver_id)

            return {
                'success': True,
                'message_id': message.id,
                'record_name': record_name,
                'status_code': 201,
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500,
            }

    def send_to_relevant_websockets(self, body, sender_id, receiver_id):
        message_data = {
            'body': body,
            'sender_id': sender_id,
            'recipient_id': receiver_id
        }
        print(f"Controller: Preparando para enviar para WebSockets - {message_data}")

        for websocket in active_websockets:
            try:
                print(
                    f"Controller: Verificando WebSocket - Sender: {websocket.get('sender_id')}, Recipient: {websocket.get('recipient_id')}")
                if (websocket['sender_id'] == sender_id and websocket['recipient_id'] == receiver_id) or \
                        (websocket['sender_id'] == receiver_id and websocket['recipient_id'] == sender_id):
                    print(f"Controller: Enviando mensagem para WebSocket correspondente")
                    asyncio.ensure_future(websocket['connection'].send(json.dumps(message_data)))
            except Exception as e:
                _logger.error(f"Error sending message to websocket: {str(e)}")


    @http.route(f'{BASE_URLS}/discuss/upload', auth='none', cors='*', type='http', methods=['POST'], csrf=False)
    def discuss_upload_attachment(self, **kwargs):
        try:
            message_id = request.params.get('message_id')
            chat_id = request.params.get('chat_id', 6)
            attachments = request.httprequest.files.getlist('attachments')

            if not message_id or not attachments:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'message_id and attachments are required',
                        'status_code': 400
                    }),
                    content_type='application/json',
                    status=400
                )

            message = request.env['mail.message'].sudo().browse(int(message_id))
            if not message.exists():
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Message not found',
                        'status_code': 404
                    }),
                    content_type='application/json',
                    status=404
                )

            attachment_ids = []
            for attachment in attachments:
                attachment_data = attachment.read()
                attachment_obj = request.env['ir.attachment'].sudo().create({
                    'name': attachment.filename,
                    'datas': base64.b64encode(attachment_data),
                    'res_model': 'mail.message',
                    'res_id': message.id,
                    'type': 'binary'
                })
                attachment_ids.append(attachment_obj.id)

            message.write({
                'attachment_ids': [(4, aid) for aid in attachment_ids]
            })

            return Response(
                json.dumps({
                    'success': True,
                    'message_id': message.id,
                    'chat_id': chat_id,
                    'attachment_ids': attachment_ids,
                    'status_code': 200
                }),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                    'status_code': 500
                }),
                content_type='application/json',
                status=500
            )

    @http.route(f'{BASE_URLS}/discuss/<int:message_id>', auth='none', cors='*', type='json', methods=['PUT'],
                csrf=False)
    def discuss_update_message(self, message_id, **kwargs):
        try:
            message = request.env['mail.message'].sudo().browse(message_id)
            if not message.exists():
                return {
                    'success': False,
                    'error': 'Message not found',
                    'status_code': 404
                }

            new_body = request.jsonrequest.get('body')

            if not new_body:
                return {
                    'success': False,
                    'error': 'Body is required for update',
                    'status_code': 400
                }

            message.write({
                'body': new_body
            })

            return {
                'success': True,
                'message_id': message.id,
                'updated_body': new_body,
                'status_code': 200
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }

    @http.route(f'{BASE_URLS}/discuss/delete', auth='none', cors='*', type='http', methods=['DELETE'], csrf=False)
    def discuss_delete_message(self, **kwargs):
        try:
            if request.httprequest.content_type.startswith('multipart/form-data'):
                message_id = request.params.get('message_id')
            else:
                data = json.loads(request.httprequest.data)
                message_id = data.get('message_id')

            if not message_id:
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'message_id is required',
                        'status_code': 400
                    }),
                    content_type='application/json',
                    status=400
                )

            message = request.env['mail.message'].sudo().browse(int(message_id))
            if not message.exists():
                return Response(
                    json.dumps({
                        'success': False,
                        'error': 'Message not found',
                        'status_code': 404
                    }),
                    content_type='application/json',
                    status=404
                )

            message.unlink()

            return Response(
                json.dumps({
                    'success': True,
                    'deleted_message_id': int(message_id),
                    'status_code': 200
                }),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return Response(
                json.dumps({
                    'success': False,
                    'error': str(e),
                    'status_code': 500
                }),
                content_type='application/json',
                status=500
            )



    @http.route('/ws_connect/', type='http', auth='none')
    async def ws_connect(self):
        print("Controller: Nova conexão WebSocket iniciada")
        websocket = websockets.connect(uri)
        connection = await websocket.__aenter__()

        ws_data = {
            'sender_id': ...,
            'recipient_id': ...,
            'connection': connection
        }

        active_websockets.append(ws_data)
        print(f"Controller: WebSocket adicionado à lista ativa - {ws_data}")

        try:
            async for message in websocket:
                print(f"Controller: Mensagem recebida via WebSocket: {message}")
                pass
        finally:
            active_websockets.remove(ws_data)
            print(f"Controller: WebSocket removido da lista ativa - {ws_data}")
            await websocket.__aexit__()

        return web.Response(text='WebSocket connection closed')

    # @token_required
    @http.route(f'{BASE_URLS}/employee/messages/<int:employee_id>', type='http', auth='none', methods=['GET'],
                csrf=False)
    def get_employee_messages(self, employee_id):
        try:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                return http.Response(json.dumps({"error": "Employee not found"}), status=404,
                                     content_type='application/json')

            if not employee.user_id or not employee.user_id.partner_id:
                return http.Response(json.dumps({"error": "No partner associated"}), status=404,
                                     content_type='application/json')

            current_partner_id = employee.user_id.partner_id.id

            domain = [
                '|',
                '|',
                ('author_id', '=', current_partner_id),
                ('partner_ids', 'in', [current_partner_id]),
                '&',
                ('model', '=', 'mail.channel'),
                ('res_id', 'in', employee.user_id.channel_ids.ids)
            ]

            messages = request.env['mail.message'].sudo().search(domain, order='date DESC')

            conversations = {}
            for message in messages:

                participants = set()

                if message.author_id:
                    participants.add(message.author_id.id)

                if message.partner_ids:
                    participants.update(message.partner_ids.ids)

                if message.model == 'mail.channel':
                    channel = request.env['mail.channel'].sudo().browse(message.res_id)
                    if channel.exists():
                        participants.update(channel.channel_partner_ids.ids)

                conversation_key = tuple(sorted(participants))

                if conversation_key not in conversations:
                    partner_records = request.env['res.partner'].sudo().browse(list(participants))
                    conversations[conversation_key] = {
                        "participants": [{
                            "id": p.id,
                            "name": p.name,
                            "email": p.email,
                            "is_me": p.id == current_partner_id
                        } for p in partner_records],
                        "messages": []
                    }

                is_sent = message.author_id.id == current_partner_id

                conversations[conversation_key]["messages"].append({
                    "id": message.id,
                    "body": message.body,
                    "date": message.date.strftime('%Y-%m-%d %H:%M:%S') if message.date else None,
                    "direction": "sent" if is_sent else "received",
                    "author": {
                        "id": message.author_id.id,
                        "name": message.author_id.name,

                    },
                    "recipients": [{
                        "id": p.id,
                        "name": p.name,

                    } for p in message.partner_ids],
                    "is_channel": message.model == 'mail.channel',
                    "channel_id": message.res_id if message.model == 'mail.channel' else None
                })

            response = {
                "employee_id": employee_id,
                "employee_name": employee.name,
                "conversations": [{
                    "conversation_id": idx + 1,
                    **data
                } for idx, data in enumerate(conversations.values())]
            }

            return http.Response(json.dumps(response, default=str), status=200,
                                 content_type='application/json')

        except Exception as e:
            return http.Response(json.dumps({"error": str(e)}), status=500,
                                 content_type='application/json')

    @http.route(f'{BASE_URLS}/employee/message_sender/<int:employee_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_employee_message_senders(self, employee_id):
        try:
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee.exists():
                return http.Response(json.dumps({"error": "Employee not found"}), status=404,
                                     content_type='application/json')

            if not employee.user_id or not employee.user_id.partner_id:
                return http.Response(json.dumps({"error": "No partner associated"}), status=404,
                                     content_type='application/json')

            current_partner_id = employee.user_id.partner_id.id

            domain = [
                '|',
                '|',
                ('partner_ids', 'in', [current_partner_id]),
                '&', ('model', '=', 'mail.channel'),
                ('res_id', 'in', employee.user_id.channel_ids.ids),
                ('author_id', '!=', current_partner_id),
            ]

            messages = request.env['mail.message'].sudo().search(domain)

            sender_ids = set(messages.mapped('author_id').ids)
            senders = request.env['res.partner'].sudo().browse(list(sender_ids))

            result = [{
                "id": sender.id,
                "name": sender.name
            } for sender in senders]

            return http.Response(json.dumps(result), status=200,
                                 content_type='application/json')

        except Exception as e:
            return http.Response(json.dumps({"error": str(e)}), status=500,
                                 content_type='application/json')

    @http.route(f'{BASE_URLS}/employee/messages/attachments/<int:employee_id>', type='http', auth='none',
                methods=['GET'], csrf=False)
    def get_employee_message_attachments(self, employee_id):
        try:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                return http.Response(json.dumps({"error": "Employee not found"}), status=404,
                                     content_type='application/json')

            if not employee.user_id or not employee.user_id.partner_id:
                return http.Response(json.dumps({"error": "No partner associated"}), status=404,
                                     content_type='application/json')

            current_partner_id = employee.user_id.partner_id.id

            domain = [
                '|',
                '|',
                ('author_id', '=', current_partner_id),
                ('partner_ids', 'in', [current_partner_id]),
                '&',
                ('model', '=', 'mail.channel'),
                ('res_id', 'in', employee.user_id.channel_ids.ids)
            ]

            messages = request.env['mail.message'].sudo().search(domain, order='date DESC')

            message_attachments = {}
            for message in messages:
                if message.attachment_ids:
                    attachments = []
                    for attachment in message.attachment_ids:
                        attachments.append({
                            "id": attachment.id,
                            "name": attachment.name,
                            "type": attachment.mimetype,
                            "size": attachment.file_size
                        })

                    message_attachments[message.id] = attachments

            response = {
                "employee_id": employee_id,
                "employee_name": employee.name,
                "message_attachments": [{
                    "message_id": message_id,
                    "attachments": attachments
                } for message_id, attachments in message_attachments.items()]
            }

            return http.Response(json.dumps(response, default=str), status=200, content_type='application/json')

        except Exception as e:
            return http.Response(json.dumps({"error": str(e)}), status=500, content_type='application/json')

    @token_required
    @http.route(f'{BASE_URLS}/employee/activities/<int:employee_id>', type='http', auth='none', methods=['GET'],
                csrf=False)
    def get_employee_activities(self, employee_id):

        Employee = request.env['hr.employee'].sudo().search([('id', '=', employee_id)], limit=1)

        if not Employee:
            response_data = json.dumps({
                "success": False,
                "error": "Employee not found",
                "status_code": 404
            })
            return werkzeug.wrappers.Response(response_data, status=404, headers=[('Content-Type', 'application/json')])

        activities = request.env['mail.activity'].sudo().search(
            [('res_model', '=', 'hr.employee'), ('res_id', '=', employee_id)])

        if not activities:
            response_data = json.dumps({
                "success": False,
                "message": "No activities found for this employee",
                "status_code": 200
            })
            return werkzeug.wrappers.Response(response_data, status=200, headers=[('Content-Type', 'application/json')])

        activity_list = []
        for activity in activities:
            activity_list.append({
                "id": activity.id,
                "activity_type": activity.activity_type_id.name,
                "summary": activity.summary,
                "note": activity.note,
                "date_deadline": activity.date_deadline.strftime('%Y-%m-%d') if activity.date_deadline else None,
                "user_responsible": activity.user_id.name if activity.user_id else None,
                "state": activity.state,
            })

        response_data = json.dumps({
            "success": True,
            "employee_id": employee_id,
            "activities": activity_list
        })
        return werkzeug.wrappers.Response(response_data, status=200, headers=[('Content-Type', 'application/json')])

    @token_required
    @http.route(f'{BASE_URLS}/employee/activity/accept', type='json', auth='none', methods=['POST'], csrf=False)
    def accept_employee_activity(self, **kwargs):
        try:
            data = request.httprequest.json
            activity_id = data.get('activity_id')
            if not activity_id:
                return {
                    'http_status': 400,
                    'message': "O campo 'activity_id' é obrigatório."
                }

            activity = request.env['mail.activity'].sudo().browse(activity_id)
            if not activity.exists():
                return {
                    'http_status': 404,
                    'error': "Atividade não encontrada."
                }

            activity.sudo().action_done()

            return {
                'http_status': 200,
                'message': "Atividade marcada como concluída com sucesso."
            }

        except ValidationError as ve:
            return {
                'http_status': 400,
                'message': ve.name
            }

        except Exception as e:
            return {
                'http_status': 500,
                'message': f"Erro interno ao processar a requisição: {str(e)}"
            }

    @token_required
    @http.route(f'{BASE_URLS}/activity/<int:activity_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_activity_by_id(self, activity_id):
        if not activity_id:
            return werkzeug.wrappers.Response(
                json.dumps({"success": False, "error": "activity_id is required", "status_code": 400}),
                content_type="application/json",
                status=400
            )

        activity = request.env['mail.activity'].sudo().browse(activity_id)

        if not activity.exists():
            return werkzeug.wrappers.Response(
                json.dumps({"success": False, "error": "Activity not found", "status_code": 404}),
                content_type="application/json",
                status=404
            )

        response_data = {
            "id": activity.id,
            "res_model": activity.res_model,
            "res_id": activity.res_id,
            "activity_type_id": activity.activity_type_id.id if activity.activity_type_id else None,
            "summary": activity.summary,
            "note": activity.note,
            "date_deadline": activity.date_deadline.strftime('%Y-%m-%d') if activity.date_deadline else None,
            "user_id": activity.user_id.id if activity.user_id else None,
            "state": activity.state,
            "create_date": activity.create_date.strftime('%Y-%m-%d %H:%M:%S') if activity.create_date else None
        }

        return werkzeug.wrappers.Response(
            json.dumps({"success": True, "data": response_data}),
            content_type="application/json",
            status=200
        )

    @token_required
    @http.route(f'{BASE_URLS}/activity/icon/<int:activity_id>', type='http', auth='none', methods=['GET'])
    def get_activity_icon(self, activity_id):
        try:
            activity = request.env['mail.activity'].sudo().browse(activity_id)
            if not activity.exists():
                return {
                    "success": False,
                    "message": "Atividade não encontrada",
                    "status_code": 404
                }

            if not activity.activity_type_id or not activity.activity_type_id.icon:
                return {
                    "success": False,
                    "message": "Ícone não disponível",
                    "status_code": 404
                }

            icon_name = activity.activity_type_id.icon
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": True,
                    "icon": icon_name,
                    "status_code": 200
                }), content_type="application/json",
                status=200
            )

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}",
                "status_code": 500
            }

    # @token_required
    @http.route(f'{BASE_URLS}/last_record/<int:employee_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_last_record(self, employee_id):
        try:
            if not employee_id:
                return werkzeug.wrappers.Response(
                    json.dumps({
                        "success": False,
                        "error": "employee_id is required",
                        "status_code": 400
                    }),
                    content_type="application/json",
                    status=400
                )

            last_record = request.env['last.record'].sudo().search(
                [('employee_id', '=', employee_id)],
                limit=1
            )

            if not last_record:
                return werkzeug.wrappers.Response(
                    json.dumps({
                        "success": False,
                        "error": "No last record found for this employee",
                        "status_code": 404
                    }),
                    content_type="application/json",
                    status=404
                )

            leave_data = {
                "name": last_record.leave_name if last_record.leave_name else None,
                "state": last_record.leave_state if last_record.leave_state else None,
            }
            loan_data = {
                "name": last_record.loan_name or '',
                "state": last_record.loan_state or '',
            }
            swap_data = {
                "state": last_record.swap_state or '',
                "date": last_record.swap_date or '',
            }
            certificate_data = {
                "name": last_record.certificate_name or '',
                "state": last_record.certificate_state or '',
                "date": last_record.certificate_date or '',
            }

            all_empty = all([
                not leave_data["name"] and not leave_data["state"],
                not loan_data["name"] and not loan_data["state"],
                not swap_data["state"] and not swap_data["date"],
                not certificate_data["name"] and not certificate_data["state"] and not certificate_data["date"],
            ])

            response_data = {
                "success": True,
                "data": {} if all_empty else {
                    "employee_id": employee_id,
                    "leave": leave_data,
                    "loan": loan_data,
                    "swap": swap_data,
                    "certificate": certificate_data
                }
            }

            return werkzeug.wrappers.Response(
                json.dumps(response_data, default=str),
                headers={'Content-Type': 'application/json'},
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": f"Internal error: {str(e)}",
                    "status_code": 500
                }),
                content_type="application/json",
                status=500
            )

    @http.route(f'{BASE_URLS}/compute_salary/<int:employee_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def compute_salary(self, employee_id):
        info = []

        if not employee_id:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "employee_id is required",
                    "status_code": 400
                }),
                headers={'Content-Type': 'application/json'},
                status=400
            )

        employee = request.env['hr.employee'].sudo().browse(employee_id)

        if not employee.exists():
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "Employee not found",
                    "status_code": 404
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        contracts = request.env['hr.contract'].sudo().search([
            ('employee_id', '=', employee_id),
            ('state', '=', 'open'),
        ], limit=1)

        if not contracts:
            return werkzeug.wrappers.Response(
                json.dumps({
                    "success": False,
                    "error": "Contract not found for this employee",
                    "status_code": 404
                }),
                headers={'Content-Type': 'application/json'},
                status=404
            )

        for contract in contracts:
            info.append({
                "employee_id": contract.employee_id.id,
                "employee_name": contract.employee_id.name,
                "contract_id": contract.id,
                "wage": contract.wage,
                'other_allowances': contract.other_allowance,

            })

        return werkzeug.wrappers.Response(
            json.dumps(info),
            headers={'Content-Type': 'application/json'},
            status=200
        )

    @http.route(f'{BASE_URLS}/payslip/<int:id>', type='http', auth='none', methods=['GET'], csrf=False)
    def payslip(self, id):
        info = []
        if not id:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'success': False,
                    'error': 'id is required',
                }),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        record = request.env['hr.payslip'].sudo().browse(id)
        if not record.exists():
            return werkzeug.wrappers.Response(
                json.dumps({
                    'success': False,
                    'error': 'No record found',
                }),
                headers=[('Content-Type', 'application/json')],
                status=404
            )

        info = {
            'id': record.id,
            'employee_id': record.employee_id.id,
            'journal_id': record.journal_id.id if record.journal_id else None,
            'journal_name': record.journal_id.name if record.journal_id else None,
        }

        return werkzeug.wrappers.Response(
            json.dumps({
                'success': True,
                'data': info,
            }),
            headers=[('Content-Type', 'application/json')],
            status=200
        )

    @http.route(f'{BASE_URLS}/payroll/download/<int:payslip_id>', type='http', auth='none', csrf=False)
    def download_payslip_pdf(self, payslip_id):
        if not payslip_id:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'success': False,
                    'error': 'Payslip ID is required',
                }),
                content_type='application/json',
                status=400
            )

        payroll_user_id = request.env.ref('base.user_admin').id

        env = request.env(user=payroll_user_id)

        payslip = env['hr.payslip'].sudo().browse(payslip_id)
        if not payslip.exists():
            return request.not_found()

        try:
            pdf_content, _ = env.ref('hr_payroll_community.action_report_payslip').sudo()._render_qweb_pdf(payslip.id)
        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({'success': False, 'error': str(e)}),
                content_type='application/json',
                status=500
            )

        pdf_filename = f"Recibo_{payslip.employee_id.name.replace(' ', '_')}.pdf"

        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="{pdf_filename}"')
            ]
        )

    @http.route(f'{BASE_URLS}/employee/messages/attachment/<int:attachment_id>', type='http', auth='none',
                methods=['GET'], csrf=False)
    def download_employee_attachment(self, attachment_id):
        try:
            attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
            if not attachment.exists():
                return http.Response(
                    json.dumps({"error": "Attachment not found"}),
                    status=404,
                    content_type='application/json'
                )

            file_data = base64.b64decode(attachment.datas)
            headers = [
                ('Content-Type', attachment.mimetype),
                ('Content-Disposition', f'attachment; filename={attachment.name}'),
                ('Content-Length', str(len(file_data)))
            ]
            return request.make_response(file_data, headers=headers)

        except Exception as e:
            return http.Response(
                json.dumps({"error": str(e)}),
                status=500,
                content_type='application/json'
            )

    @http.route(f'{BASE_URLS}/employee/messages/attachments/<int:employee_id>', type='http', auth='none',
                methods=['GET'], csrf=False)
    def get_employee_message_attachments(self, employee_id):

        BASE_URLS = '/api'

        try:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                return http.Response(
                    json.dumps({"error": "Employee not found"}),
                    status=404,
                    content_type='application/json'
                )

            if not employee.user_id or not employee.user_id.partner_id:
                return http.Response(
                    json.dumps({"error": "No partner associated"}),
                    status=404,
                    content_type='application/json'
                )

            current_partner_id = employee.user_id.partner_id.id

            domain = [
                '|',
                '|',
                ('author_id', '=', current_partner_id),
                ('partner_ids', 'in', [current_partner_id]),
                '&',
                ('model', '=', 'mail.channel'),
                ('res_id', 'in', employee.user_id.channel_ids.ids)
            ]

            messages = request.env['mail.message'].sudo().search(domain, order='date DESC')

            message_attachments = []
            for message in messages:
                if message.attachment_ids:
                    attachments = []
                    for attachment in message.attachment_ids:
                        attachments.append({
                            "id": attachment.id,
                            "name": attachment.name,
                            "type": attachment.mimetype,
                            "size": attachment.file_size,
                            "url": f"/employee/messages/attachment/{attachment.id}"
                        })

                    message_attachments.append({
                        "message_id": message.id,
                        "attachments": attachments
                    })

            response = {
                "employee_id": employee_id,
                "employee_name": employee.name,
                "message_attachments": message_attachments
            }

            return http.Response(
                json.dumps(response, default=str),
                status=200,
                content_type='application/json'
            )

        except Exception as e:
            return http.Response(
                json.dumps({"error": str(e)}),
                status=500,
                content_type='application/json'
            )

    @http.route(f'{BASE_URLS}/discuss/upload_audio', auth='none', type='http', methods=['POST'], csrf=False, cors='*')
    def upload_audio(self, **kwargs):
        try:
            message_id = request.params.get('message_id')
            uploaded_file = request.httprequest.files.get('audio')

            if not message_id or not uploaded_file:
                return Response(json.dumps({
                    'success': False,
                    'error': 'message_id and audio file are required'
                }), content_type='application/json', status=400)

            original_audio_data = uploaded_file.read()
            original_extension = uploaded_file.filename.split('.')[-1].lower()


            original_audio = AudioSegment.from_file(io.BytesIO(original_audio_data), format=original_extension)
            mp3_buffer = io.BytesIO()
            original_audio.export(mp3_buffer, format='mp3')
            mp3_data = mp3_buffer.getvalue()

            message = request.env['mail.message'].sudo().browse(int(message_id))
            if not message.exists():
                return Response(json.dumps({
                    'success': False,
                    'error': 'Message not found'
                }), content_type='application/json', status=404)

            attachment = request.env['ir.attachment'].sudo().create({
                'name': 'voice_message.mp3',
                'datas': base64.b64encode(mp3_data),
                'mimetype': 'audio/mpeg',
                'res_model': 'mail.message',
                'res_id': message.id,
                'type': 'binary',
            })

            message.write({
                'attachment_ids': [(4, attachment.id)]
            })

            return Response(json.dumps({
                'success': True,
                'attachment_id': attachment.id
            }), content_type='application/json', status=200)

        except Exception as e:
            return Response(json.dumps({
                'success': False,
                'error': str(e)
            }), content_type='application/json', status=500)

    @http.route(f'{BASE_URLS}/payslip', type='json', auth='none', methods=['POST'], csrf=False)
    def simulate_payslip(self, **kwargs):
        data = request.jsonrequest

        structuredata = []

        required_fields = ['employee_id', 'date_from', 'date_to']
        if not all(field in data for field in required_fields):
            return {
                'error': f'Campos obrigatórios: {", ".join(required_fields)}',
                'success': False
            }

        try:
            contract = request.env['hr.contract'].sudo().search([
                ('employee_id', '=', data['employee_id']),
                ('state', '=', 'open'),
                ('date_start', '<=', data['date_to']),
                '|', ('date_end', '=', False), ('date_end', '>=', data['date_from'])
            ], limit=1)

            if not contract:
                return {
                    'error': 'Nenhum contrato válido encontrado para o funcionário no período',
                    'success': False
                }

            contract_struct_id = contract.struct_id.id
            contract_struct_name = contract.struct_id.name
            contract_name = contract.name or f"Contrato {contract.id}"

            structures = request.env['hr.payroll.structure'].sudo().browse(contract_struct_id)

            for structure in structures:
                structuredata.extend([{
                    'name': structure.id,
                    'code': structure.code,
                    'rule_ids': {
                        'structure': structure.id,
                        'name': rule.name,
                        'code': rule.code,

                        'amount_python_compute': rule.amount_python_compute,
                    }
                } for rule in structure.rule_ids])

            return {
                'success': True,
                'contract_data': {
                    'id': contract.id,
                    'name': contract_name,
                    'struct_id': contract_struct_id,
                    'struct_name': contract_struct_name,
                    'structure': structuredata,
                    'wage': contract.wage,
                    'other_allowance': contract.other_allowance,
                },
                'message': 'Dados do contrato coletados com sucesso'
            }

        except UserError as e:
            return {'error': str(e), 'success': False}
        except Exception as e:
            return {'error': f'Erro inesperado: {str(e)}', 'success': False}

    @http.route('/api/payslip/calculation', type='json', auth='none', methods=['POST'], csrf=False)
    def advanced_salary_calculation(self, **kwargs):
        data = request.jsonrequest

        try:

            required_fields = ['employee_id', 'date_from', 'date_to']
            if not all(field in data for field in required_fields):
                return {
                    'error': f'Campos obrigatórios: {", ".join(required_fields)}',
                    'success': False
                }

            contract = request.env['hr.contract'].sudo().search([
                ('employee_id', '=', data['employee_id']),
                ('state', '=', 'open'),

            ], limit=1)
            if not contract.exists():
                return {"success": False, "error": "Contrato não encontrado"}

            basic = self._calculate_basic(contract)
            allowance = self._calculate_allowance(contract)

            additions = {}
            deductions = {}

            absent_days = self._look_for_fouls(data['employee_id'], data['date_from'], data['date_to'])
            deductions['absence'] = self._calculate_dis_f_d(basic, allowance, absent_days)

            if data.get('extra_hours'):
                additions['extra_50'] = self._calculate_h_e_150(basic, allowance, data['extra_hours'].get('h_e_150', 0))
                additions['extra_100'] = self._calculate_h_e_200(basic, allowance,
                                                                 data['extra_hours'].get('h_e_200', 0))

            if data.get('deductions'):
                deductions['loan'] = self._calculate_dpe(data['deductions'].get('DPE', 0))
                deductions['funeral'] = self._calculate_dff(data['deductions'].get('DFF', 0))
                deductions['late'] = self._calculate_d_p_a(basic, allowance, data['deductions'].get('D_P_A', 0))

            gross = self._calculate_gross(basic, allowance, sum(additions.values()))
            inss = self._calculate_inss(gross)
            taxable_income = gross - inss
            irps = self._calculate_irps(taxable_income, contract.employee_id.children)
            total_deductions = inss + irps + sum(deductions.values())
            net = gross - total_deductions

            return {
                "success": True,
                "result": {
                    "components": {
                        "basic": basic,
                        "allowance": allowance,
                        "additions": additions,
                        "gross": gross
                    },
                    "deductions": {
                        "INSS": inss,
                        "IRPS": irps,
                        "others": deductions,
                        "total": total_deductions
                    },
                    "net_salary": net,
                    "currency": "MZN"
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_basic(self, contract):

        return contract.wage

    def _calculate_allowance(self, contract):

        return contract.other_allowance or 0

    def _calculate_inss(self, gross):
        """INSS (3% do bruto)"""
        return gross * 0.03

    def _calculate_dpe(self, amount):

        return abs(float(amount))

    def _calculate_dff(self, amount):

        return abs(float(amount))

    def _calculate_dis_f_d(self, basic_salary, allowance, days_absent):

        daily_salary = (basic_salary + allowance) / 30
        return daily_salary * abs(float(days_absent))

    def _calculate_d_p_a(self, basic_salary, allowance, late_hours):

        hourly_salary = ((basic_salary + allowance) / 30) / 8
        return hourly_salary * abs(float(late_hours))

    def _calculate_h_e_150(self, basic_salary, allowance, extra_hours):

        hourly_rate = ((basic_salary + allowance) / 30) / 8
        return hourly_rate * float(extra_hours) * 1.5

    def _calculate_h_e_200(self, basic_salary, allowance, extra_hours):

        hourly_rate = ((basic_salary + allowance) / 30) / 8
        return hourly_rate * float(extra_hours) * 2.0

    def _calculate_gross(self, basic, allowance, bonuses=0):

        return basic + allowance + bonuses

    def _calculate_irps(self, taxable_income, children=0):

        children = min(int(children), 3)

        if taxable_income <= 20250:
            return 0
        elif 20250 < taxable_income <= 20749.99:
            return (taxable_income - 20250) * 0.10

        else:
            return max(taxable_income * 0.32 - 28225, 0)

    def _look_for_fouls(self, employee_id, date_from, date_to):
        busca = request.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee_id),
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('state', 'in', ['confirm', 'refuse']),
        ])

        total_dias = 0
        for dado in busca:
            dias = (dado.date_to - dado.date_from).days + 1
            total_dias += dias

        return total_dias
