# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta, datetime, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from pytz import timezone, UTC


class PontualJS(models.Model):
    _name = 'pontual_js.pontual_js'
    _description = 'pontual_js.pontual_js'

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        readonly=True,
        copy=False,
        help="Empresa",
        default=lambda self: self.env.company
    )

    @api.model
    def get_pontual_js_data(self, start_date, end_date, company_id):

        print(start_date, end_date, company_id)

        employees = self.env['hr.employee'].sudo().search([
            ('company_id', '=', company_id),
            ('active', '=', True)
        ])
        total_employees = len(employees)
        employee_ids = employees.ids
        employee_dict = {emp.id: emp.name for emp in employees}

        checkins = self.env['hr.attendance'].sudo().search([
            ('check_in', '>=', start_date),
            ('check_in', '<=', end_date),
            ('employee_id', 'in', employee_ids)
        ])
        checked_in_employee_ids = checkins.mapped('employee_id.id')

        present_ids = set(checked_in_employee_ids)
        absent_ids = set(employee_ids) - present_ids

        presents = [employee_dict[emp_id] for emp_id in present_ids]
        absents = [employee_dict[emp_id] for emp_id in absent_ids]

        atrasos = self._look_for_late_arrivals(start_date, end_date)
        total_atrasos = len(atrasos)

        attendance_by_day = self._look_for_fouls(start_date, end_date, company_id)

        percent_presents = (len(presents) / total_employees) * 100 if total_employees else 0
        percent_absents = (len(absents) / total_employees) * 100 if total_employees else 0
        percent_atrasos = (total_atrasos / len(presents)) * 100 if len(presents) else 0

        return {
            'total_presents': len(presents),
            'percent_presents': round(percent_presents, 2),
            'present_list': presents,
            'total_employees': total_employees,
            'total_absents': len(absents),
            'percent_absents': round(percent_absents, 2),
            'absent_list': absents,
            'total_atrasos': total_atrasos,
            'percent_atrasos': round(percent_atrasos, 2),
            'atrasos_list': atrasos,
            'attendance_by_day': attendance_by_day,
        }

    def _look_for_fouls(self, start_date, end_date, company_id):
        print(start_date, end_date, company_id)

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        employees = self.env['hr.employee'].sudo().search([('company_id', '=', int(company_id))])
        total_employees = len(employees)
        attendance_by_day = []

        current_date = start_date
        while current_date <= end_date:
            presentes_dia = 0
            ausentes_dia = 0

            for employee in employees:
                attendance = self.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', datetime.combine(current_date, datetime.min.time())),
                    ('check_in', '<=', datetime.combine(current_date, datetime.max.time()))
                ])

                if attendance:
                    presentes_dia += 1
                else:
                    ausentes_dia += 1


            attendance_by_day.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'day_of_week': current_date.strftime('%A'),
                'presentes': presentes_dia,
                'ausentes': ausentes_dia,
            })

            current_date += timedelta(days=1)

        return attendance_by_day

    def _look_for_late_arrivals(self, start_date, end_date):
        attendance_records = self.env['hr.attendance'].sudo().search([
            ('check_in', '>=', start_date),
            ('check_in', '<=', end_date),
        ])

        atrasos = []

        user_tz = self.env.user.tz or 'UTC'
        timezone = pytz.timezone(user_tz)

        for attendance in attendance_records:
            employee = attendance.employee_id

            check_in_utc = attendance.check_in
            if isinstance(check_in_utc, str):
                check_in_utc = datetime.strptime(check_in_utc, DEFAULT_SERVER_DATETIME_FORMAT)

            check_in_local = pytz.utc.localize(check_in_utc).astimezone(timezone)
            check_in_time = check_in_local.time()
            day_of_week = check_in_local.weekday()

            work_day = self.work_days(employee, day_of_week)

            if work_day and work_day['employee_id'] == employee.id:
                expected_time = work_day['hour_from']

                if check_in_time > expected_time:
                    delay_minutes = (datetime.combine(date.today(), check_in_time) -
                                     datetime.combine(date.today(), expected_time)).total_seconds() / 60

                    atrasos.append({
                        'id': employee.id,
                        'name': employee.name,
                        'minutes_late': int(delay_minutes),
                        'date': check_in_local.strftime('%Y-%m-%d'),
                    })
                else:
                    print("Sem atraso.")

        return atrasos

    @api.model
    def work_days(self, employee, day_of_week):

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
                hour_from = datetime.strptime(f"{int(attendance.hour_from):02d}:00", "%H:%M").time()
                hour_to = datetime.strptime(f"{int(attendance.hour_to):02d}:00", "%H:%M").time()

                if attendance.day_period == 'morning':
                    morning_from = hour_from
                    morning_to = hour_to
                elif attendance.day_period == 'afternoon':
                    afternoon_from = hour_from
                    afternoon_to = hour_to

            except ValueError as e:
                raise ValueError(f"Erro ao processar horários para {employee.name}: {e}")

        return {
            'employee_id': employee.id,
            'morning_from': morning_from,
            'morning_to': morning_to,
            'afternoon_from': afternoon_from,
            'afternoon_to': afternoon_to,
            'hour_from': morning_from if morning_from else afternoon_from,
            'hour_to': afternoon_to if afternoon_to else morning_to,
        }

