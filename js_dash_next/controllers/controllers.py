# -*- coding: utf-8 -*-
import json
from collections import defaultdict

import werkzeug.wrappers

from odoo import http, fields
from odoo.http import request
from datetime import datetime, time, timedelta
from odoo.addons.authmodel.controllers.decorators.token_required import token_required

class JsDashNext(http.Controller):

    BASE_URLS = '/api'


    @http.route(f'{BASE_URLS}/employee/<int:company_id>', auth='public' ,csrf=False, methods=['GET',] )
    def get_employee(self, company_id):
        info = []
        if not company_id:
            return  werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'company_id is required',
                    'status': 400,
                }),headers=[{'Content-Type', 'application/json'}],
                status=400
            )


        employees = request.env['hr.employee'].sudo().search([
            ('company_id', '=', company_id),
            ('active', '=', True),
        ])

        if not employees:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'employee not found',
                    'status': 404,
                }),headers=[{'Content-Type', 'application/json'}],
                status=404
            )


        for employee in employees:
            info.append({
                'id': employee.id,
                'name': employee.name,
                'job_title': employee.job_title,
                'department': employee.department_id.name,

            })

        return werkzeug.wrappers.Response(
            json.dumps({
                'success': True,
                'employees': info,
            }),headers=[{'Content-Type', 'application/json'}],
            status=200
        )

    @http.route(f'{BASE_URLS}/employee/attendance', auth='public', csrf=False, methods=['GET'])
    def get_employee_attendance(self, **kwargs):
        info = []
        company_id = kwargs.get('company_id')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')

        if not company_id or not start_date or not end_date:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'company_id, start_date and end_date are required',
                    'status': 400,
                }),
                content_type='application/json',
                status=400
            )

        try:
            start_date_dt = fields.Datetime.to_datetime(start_date)
            end_date_dt = fields.Datetime.to_datetime(end_date)
        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'Invalid date format',
                    'details': str(e),
                    'status': 400,
                }),
                content_type='application/json',
                status=400
            )

        employees = request.env['hr.employee'].sudo().search([
            ('company_id', '=', int(company_id)),
            ('active', '=', True),
        ])

        if not employees:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'No active employees found for this company',
                    'status': 404,
                }),
                content_type='application/json',
                status=404
            )

        attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', 'in', employees.ids),
            ('check_in', '>=', start_date_dt),
            ('check_in', '<=', end_date_dt),
        ], order='check_in asc')

        for att in attendances:
            info.append({
                'employee_id': att.employee_id.id,
                'employee_name': att.employee_id.name,
                'check_in': att.check_in.strftime('%Y-%m-%d'),
                'check_out': att.check_out.strftime('%Y-%m-%d') if att.check_out else '',

            })

        return werkzeug.wrappers.Response(
            json.dumps({
                'data': info,
                'status': 200,
            }),
            content_type='application/json',
            status=200
        )

    # @http.route(f'{BASE_URLS}/employee/attendance_summary', auth='public', csrf=False, methods=['GET'])
    # def get_employee_attendance_summary(self, **kwargs):
    #     company_id = kwargs.get('company_id')
    #     start_date = kwargs.get('start_date')
    #     end_date = kwargs.get('end_date')
    #
    #     if not company_id or not start_date or not end_date:
    #         return werkzeug.wrappers.Response(
    #             json.dumps({
    #                 'error': 'company_id, start_date and end_date are required',
    #                 'status': 400,
    #             }),
    #             content_type='application/json',
    #             status=400
    #         )
    #
    #     try:
    #         start_dt = fields.Datetime.to_datetime(start_date).replace(hour=0, minute=0, second=0)
    #         end_dt = fields.Datetime.to_datetime(end_date).replace(hour=23, minute=59, second=59)
    #
    #         if start_dt > end_dt:
    #             raise ValueError("start_date cannot be after end_date")
    #
    #     except Exception as e:
    #         return werkzeug.wrappers.Response(
    #             json.dumps({
    #                 'error': 'Invalid date parameters',
    #                 'details': str(e),
    #                 'status': 400,
    #             }),
    #             content_type='application/json',
    #             status=400
    #         )
    #
    #     employees = request.env['hr.employee'].sudo().search([
    #         ('company_id', '=', int(company_id)),
    #         ('active', '=', True),
    #     ])
    #
    #     if not employees:
    #         return werkzeug.wrappers.Response(
    #             json.dumps({
    #                 'error': 'No active employees found for this company',
    #                 'status': 404,
    #             }),
    #             content_type='application/json',
    #             status=404
    #         )
    #
    #     present_attendances = request.env['hr.attendance'].sudo().search([
    #         ('employee_id', 'in', employees.ids),
    #         ('check_in', '>=', start_dt),
    #         ('check_in', '<=', end_dt),
    #     ])
    #
    #     present_employee_ids = list(set(present_attendances.mapped('employee_id.id')))
    #     present_count = len(present_employee_ids)
    #
    #     absent_count = len(employees) - present_count
    #
    #     present_employees = []
    #     absent_employees = []
    #
    #     for emp in employees:
    #         emp_data = {
    #             'id': emp.id,
    #             'name': emp.name,
    #             'department': emp.department_id.name if emp.department_id else None,
    #             'job_title': emp.job_title or None
    #         }
    #
    #         if emp.id in present_employee_ids:
    #             emp_attendances = present_attendances.filtered(lambda a: a.employee_id.id == emp.id)
    #
    #
    #             emp_data.update({
    #                 'attendance_count': len(emp_attendances)
    #             })
    #             present_employees.append(emp_data)
    #         else:
    #             absent_employees.append(emp_data)
    #
    #     return werkzeug.wrappers.Response(
    #         json.dumps({
    #             'summary': {
    #                 'total_employees': len(employees),
    #                 'present_count': present_count,
    #                 'absent_count': absent_count,
    #                 'date_range': {
    #                     'start_date': start_date,
    #                     'end_date': end_date
    #                 },
    #                 'company_id': company_id,
    #             },
    #             'details': {
    #                 'present_employees': [{
    #                     **emp,
    #
    #                 } for emp in present_employees],
    #                 'absent_employees': absent_employees
    #             },
    #             'status': 200,
    #         }, default=str),
    #         content_type='application/json',
    #         status=200
    #     )
    # @token_required
    @http.route(f'{BASE_URLS}/employee/attendance_summary', auth='public', csrf=False, methods=['GET'])
    def get_employee_attendance_summary(self, **kwargs):
        company_id = kwargs.get('company_id')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')

        # Validação dos parâmetros obrigatórios
        if not company_id or not start_date or not end_date:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'company_id, start_date and end_date are required',
                    'status': 400,
                }),
                content_type='application/json',
                status=400
            )

        try:
            # Conversão e validação das datas
            start_dt = fields.Datetime.to_datetime(start_date).replace(hour=0, minute=0, second=0)
            end_dt = fields.Datetime.to_datetime(end_date).replace(hour=23, minute=59, second=59)

            if start_dt > end_dt:
                raise ValueError("start_date cannot be after end_date")

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'Invalid date parameters',
                    'details': str(e),
                    'status': 400,
                }),
                content_type='application/json',
                status=400
            )

        # Busca dos funcionários ativos da empresa
        employees = request.env['hr.employee'].sudo().search([
            ('company_id', '=', int(company_id)),
            ('active', '=', True),
        ])

        if not employees:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'No active employees found for this company',
                    'status': 404,
                }),
                content_type='application/json',
                status=404
            )

        # Busca todos os atendances no período
        present_attendances = request.env['hr.attendance'].sudo().search([
            ('employee_id', 'in', employees.ids),
            ('check_in', '>=', start_dt),
            ('check_in', '<=', end_dt),
        ], order='check_in')

        # Preparação das estruturas de dados
        present_employee_ids = set()
        late_employees_info = {}
        daily_summary = {}

        # Inicializa o daily_summary para todos os dias no intervalo
        current_date = start_dt.date()
        end_date_only = end_dt.date()

        while current_date <= end_date_only:
            daily_summary[str(current_date)] = {
                'present_count': 0,
                'absent_count': len(employees),
                'late_count': 0,
                'late_minutes': 0,
                'present_employee_ids': set()
            }
            current_date += timedelta(days=1)

        # Processamento dos atendances
        for att in present_attendances:
            emp = att.employee_id
            check_in_date = fields.Datetime.to_datetime(att.check_in).date()
            str_date = str(check_in_date)

            # Atualiza totais globais
            present_employee_ids.add(emp.id)

            # Atualiza daily summary
            day_data = daily_summary[str_date]
            day_data['present_employee_ids'].add(emp.id)
            day_data['present_count'] = len(day_data['present_employee_ids'])
            day_data['absent_count'] = len(employees) - day_data['present_count']

            # Verifica atrasos
            check_in_time = fields.Datetime.to_datetime(att.check_in).time()
            day_of_week = check_in_date.weekday()
            schedule = self._get_employee_schedule(emp, day_of_week)

            if schedule and schedule['hour_from']:
                scheduled_time = datetime.strptime(schedule['hour_from'], '%H:%M').time()
                if check_in_time > scheduled_time:
                    delta = datetime.combine(check_in_date, check_in_time) - datetime.combine(check_in_date,
                                                                                              scheduled_time)
                    late_minutes = int(delta.total_seconds() / 60)

                    # Atualiza totais de atraso
                    day_data['late_count'] += 1
                    day_data['late_minutes'] += late_minutes

                    # Mantém registro dos atrasos por funcionário
                    if emp.id not in late_employees_info:
                        late_employees_info[emp.id] = {
                            'employee': emp,
                            'total_late_minutes': 0,
                            'late_days': 0,
                            'attendances': []
                        }

                    late_employees_info[emp.id]['total_late_minutes'] += late_minutes
                    late_employees_info[emp.id]['late_days'] += 1
                    late_employees_info[emp.id]['attendances'].append({
                        'date': check_in_date.strftime('%Y-%m-%d'),
                        'check_in': att.check_in.strftime('%Y-%m-%d %H:%M:%S'),
                        'late_minutes': late_minutes
                    })

        # Cálculo dos totais globais
        present_count = len(present_employee_ids)
        absent_count = len(employees) - present_count
        late_employees_count = len(late_employees_info)
        total_late_minutes = sum(info['total_late_minutes'] for info in late_employees_info.values())

        # Preparação dos dados de retorno
        present_employees = []
        absent_employees = []
        late_employees = []

        for emp in employees:
            emp_data = {
                'id': emp.id,
                'name': emp.name,
                'department': emp.department_id.name if emp.department_id else None,
                'job_title': emp.job_title or None
            }

            if emp.id in present_employee_ids:
                emp_data.update({
                    'attendance_count': len([a for a in present_attendances if a.employee_id.id == emp.id]),
                    'late_minutes': late_employees_info.get(emp.id, {}).get('total_late_minutes', 0),
                    'late_days': late_employees_info.get(emp.id, {}).get('late_days', 0)
                })
                present_employees.append(emp_data)
            else:
                absent_employees.append(emp_data)

            if emp.id in late_employees_info:
                late_employees.append(emp_data)

        # Formata o daily_summary para o retorno (remove sets internos)
        formatted_daily_summary = {
            date: {
                k: v for k, v in data.items() if k != 'present_employee_ids'
            }
            for date, data in daily_summary.items()
        }

        return werkzeug.wrappers.Response(
            json.dumps({
                'summary': {
                    'total_employees': len(employees),
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'total_late_minutes': total_late_minutes,
                    'late_employees_count': late_employees_count,
                    'date_range': {
                        'start_date': start_date,
                        'end_date': end_date
                    },
                    'company_id': company_id,
                },
                'details': {
                    'present_employees': present_employees,
                    'absent_employees': absent_employees,
                    'late_employees': {
                        'count': late_employees_count,
                        'total_late_minutes': total_late_minutes,
                        'list': late_employees
                    }
                },
                'daily_summary': formatted_daily_summary,
                'status': 200,
            }, default=str),
            content_type='application/json',
            status=200
        )

    def _get_employee_schedule(self, employee, day_of_week):
        """Helper method to get employee schedule for a specific day"""
        if not employee.resource_calendar_id:
            return None

        attendances = employee.resource_calendar_id.attendance_ids.filtered(
            lambda a: int(a.dayofweek) == day_of_week
        )

        morning_from = None
        morning_to = None
        afternoon_from = None
        afternoon_to = None

        for attendance in attendances:
            try:
                hour_from = time(int(attendance.hour_from), 0)
                hour_to = time(int(attendance.hour_to), 0)

                if attendance.day_period == 'morning':
                    morning_from = hour_from
                    morning_to = hour_to
                elif attendance.day_period == 'afternoon':
                    afternoon_from = hour_from
                    afternoon_to = hour_to

            except ValueError as e:
                raise ValueError(f"Error processing schedule for {employee.name}: {e}")

        hour_from = morning_from or afternoon_from
        hour_to = afternoon_to or morning_to

        return {
            'morning_from': morning_from.strftime('%H:%M') if morning_from else None,
            'morning_to': morning_to.strftime('%H:%M') if morning_to else None,
            'afternoon_from': afternoon_from.strftime('%H:%M') if afternoon_from else None,
            'afternoon_to': afternoon_to.strftime('%H:%M') if afternoon_to else None,
            'hour_from': hour_from.strftime('%H:%M') if hour_from else None,
            'hour_to': hour_to.strftime('%H:%M') if hour_to else None,
        }

    @token_required
    @http.route(f'{BASE_URLS}/employee/allowed_companies/<int:employee_id>', auth='public', csrf=False, methods=['GET'])
    def get_employee_allowed_companies(self, employee_id):

        if not employee_id:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'employee_id is required',
                    'status': 400,
                }),
                content_type='application/json',
                status=400
            )

        try:
            employee = request.env['hr.employee'].sudo().browse(int(employee_id))
            if not employee.exists():
                return werkzeug.wrappers.Response(
                    json.dumps({
                        'error': 'Employee not found',
                        'status': 404,
                    }),
                    content_type='application/json',
                    status=404
                )

            user = employee.user_id
            if not user:
                return werkzeug.wrappers.Response(
                    json.dumps({
                        'error': 'No user associated with this employee',
                        'status': 404,
                    }),
                    content_type='application/json',
                    status=404
                )

            allowed_companies = user.company_ids

            response_data = [{
                'id': company.id,
                'name': company.name
            } for company in allowed_companies]

            return werkzeug.wrappers.Response(
                json.dumps({
                    'data': response_data,
                    'status': 200,
                }, default=str),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return werkzeug.wrappers.Response(
                json.dumps({
                    'error': 'Internal server error',
                    'details': str(e),
                    'status': 500,
                }),
                content_type='application/json',
                status=500
            )
