# -*- coding: utf-8 -*-
import base64
import json
from datetime import datetime, time

from odoo import http
import werkzeug
from odoo.http import request, HttpRequest
from odoo.addons.authmodel.controllers.decorators.token_required import token_required

import pytz
from pytz import timezone, UTC


class JsPontualCandidate(http.Controller):
    BASE_URL = '/api/employees'
    BASE_URL_LEAVE = '/api/leave'

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

    @token_required
    @http.route(f"{BASE_URL}/<int:employee_id>/image", type='http', auth='none', cors='*', csrf=False,
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

    @token_required
    @http.route(f"{BASE_URL}/<int:employee_id>/announcements", type='http', auth='none', cors='*', csrf=False,
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
                "status_code":404,
                "error": "No announcements found for this department"
            })
            return werkzeug.wrappers.Response(
                response_data,
                status=404,
                headers=[('Content-Type', 'application/json')]
            )

        announcements_data = []
        for announcement in announcements:
            announcements_data.append({
                'id': announcement.id,
                'title': announcement.announcement_reason,
                'announcement': announcement.announcement,
                'date_start': announcement.date_start.strftime('%Y-%m-%d'),
                'department': ', '.join([dept.name for dept in announcement.department_ids]),
            })

        return werkzeug.wrappers.Response(
            json.dumps({"announcements": announcements_data}),
            status=200,
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

    @http.route(f"{BASE_URL_LEAVE}/time-offs", type='json', auth='user', methods=['POST'])
    def create_time_off(self):
        try:
            data = request.jsonrequest

            maputo_tz = pytz.timezone('Africa/Maputo')
            utc_tz = pytz.utc

            required_fields = ['employee_id', 'leave_type_id', 'date_from', 'date_to']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "status_code": 400,
                }

            employee_id = data['employee_id']
            leave_type_id = data['leave_type_id']
            date_from_str = data['date_from']
            date_to_str = data['date_to']
            description = data.get("description", "")

            try:
                naive_dt_from = datetime.strptime(date_from_str, '%Y-%m-%d %H:%M:%S')
                dt_from = maputo_tz.localize(naive_dt_from)

                naive_dt_to = datetime.strptime(date_to_str, '%Y-%m-%d %H:%M:%S')
                dt_to = maputo_tz.localize(naive_dt_to)
            except ValueError:
                return {
                    "success": False,
                    "error": "Invalid date format. Use 'YYYY-MM-DD HH:MM:SS'",
                    "status_code": 400,
                }

            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee.exists():
                return {
                    "success": False,
                    "error": "Employee not found",
                    "status_code": 404,
                }

            leave_type = request.env['hr.leave.type'].sudo().browse(leave_type_id)
            if not leave_type.exists():
                return {
                    "success": False,
                    "error": "Leave Type ID inválido",
                    "status_code": 400,
                }

            day_of_week = dt_from.weekday()
            work_schedule = self.work_days(employee.resource_calendar_id, day_ofweek=day_of_week)

            if not work_schedule:
                return {
                    "success": False,
                    "error": "No working schedule found for this day",
                    "status_code": 400,
                }

            work_day = work_schedule[0]

            request_date_from = maputo_tz.localize(datetime.combine(dt_from.date(), work_day['hour_from']))
            request_date_to = maputo_tz.localize(datetime.combine(dt_to.date(), work_day['hour_to']))

            leave_vals = {
                "employee_id": employee_id,
                'holiday_status_id': leave_type.id,
                "date_from": dt_from.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S'),
                "date_to": dt_to.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S'),
                'request_date_from': request_date_from.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S'),
                'request_date_to': request_date_to.astimezone(utc_tz).strftime('%Y-%m-%d %H:%M:%S'),
                "state": "confirm",
                "name": description,
            }

            leave = request.env['hr.leave'].sudo().create(leave_vals)

            return {
                "success": True,
                "message": "Time off created successfully",
                "data": {
                    "time_off_id": leave.id,
                    "employee_id": employee_id,
                    "dates": {
                        "from": dt_from.strftime('%Y-%m-%d %H:%M:%S'),
                        "to": dt_to.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    "request_dates": {
                        "from": request_date_from.strftime('%Y-%m-%d %H:%M:%S'),
                        "to": request_date_to.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    "timezone": "Africa/Maputo (UTC+2)"
                },
                "status_code": 201,
            }

        except Exception as e:
            import traceback
            error_message = traceback.format_exc()
            return {
                "success": False,
                "error": str(e),
                "traceback": error_message,
                "status_code": 500,
            }

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



