# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date

import pytz
from pytz import timezone, UTC

from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []

        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

        fouls = self._look_for_fouls(date_from, date_to)
        attendances = self._look_for_late_arrivals(date_from, date_to)
        overtimes = self._look_for_overtime(date_from, date_to)



        for contract in contracts:
            for input in inputs:
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'amount': 0,
                    'contract_id': contract.id,
                }

                if input.code == "TO_F_D":
                    total_faltas = sum(1 for falta in fouls if falta['id'] == contract.employee_id.id)
                    input_data['amount'] = total_faltas

                if input.code == "D_P_A":
                    employee_id = int(contract.employee_id.id)

                    total_atrasos = sum(
                        atraso['minutes_late'] for atraso in attendances if int(atraso['id']) == employee_id
                    )

                    input_data['amount'] = total_atrasos / 60

                if input.code == "H_E_150":
                    total_extras = sum(
                        extra['minutes_extra'] for extra in overtimes if extra['id'] == contract.employee_id.id)
                    input_data['amount'] = round(total_extras / 60, 2)

                res.append(input_data)

        return res

    def _look_for_fouls(self, date_from, date_to):

        busca = self.env['hr.leave'].sudo().search([
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('state', 'in', ['confirm', 'refuse']),
        ])

        dados = []
        for dado in busca:
            dados.append({
                'id': dado.employee_id.id,
                'name': dado.employee_id.name,
                'date_from': dado.date_from.strftime('%Y-%m-%d'),
                'date_to': dado.date_to.strftime('%Y-%m-%d'),
            })

        return dados

    def _look_for_late_arrivals(self, date_from, date_to):
        attendance_records = self.env['hr.attendance'].sudo().search([
            ('check_in', '>=', date_from),
            ('check_in', '<=', date_to),
        ])

        atrasos = []

        for attendance in attendance_records:
            employee = attendance.employee_id
            check_in_time = attendance.check_in.time()

            day_of_week = attendance.check_in.weekday()

            # Corrigido: Passando 'employee' como argumento
            work_days = self.work_days(employee, day_of_week)

            for work_day in work_days:
                if work_day['employee_id'] == employee.id:
                    expected_time = work_day['hour_from']

                    if check_in_time > expected_time:
                        delay_minutes = (datetime.combine(date.today(), check_in_time) -
                                         datetime.combine(date.today(), expected_time)).total_seconds() / 60

                        atrasos.append({
                            'id': employee.id,
                            'name': employee.name,
                            'minutes_late': int(delay_minutes),
                            'date': attendance.check_in.strftime('%Y-%m-%d'),
                        })

        return atrasos

    def _look_for_overtime(self, date_from, date_to):
        """Busca horas extras dos funcionários dentro do período informado, convertendo timezone corretamente."""

        user_tz = timezone(self.env.user.tz) if self.env.user.tz else UTC

        attendance_records = self.env['hr.attendance'].sudo().search([
            ('check_out', '>=', date_from),
            ('check_out', '<=', date_to),
        ])

        horas_extras = []

        for attendance in attendance_records:
            employee = attendance.employee_id

            check_out_utc = attendance.check_out
            check_out_local = UTC.localize(check_out_utc).astimezone(user_tz)
            check_out_time = check_out_local.time()
            day_of_week = check_out_local.weekday()

            work_days = self.work_days(employee, day_of_week)

            print(check_out_local.strftime('%Y-%m-%d %H:%M'))

            for work_day in work_days:
                expected_time = work_day.get('hour_to')

                if expected_time and check_out_time > expected_time:
                    overtime_minutes = (datetime.combine(date.today(), check_out_time) -
                                        datetime.combine(date.today(), expected_time)).total_seconds() / 60

                    print(f"Funcionário: {employee.name} | Horas extras (minutos): {int(overtime_minutes)}")

                    horas_extras.append({
                        'id': employee.id,
                        'name': employee.name,
                        'minutes_extra': int(overtime_minutes),
                        'date': check_out_local.strftime('%Y-%m-%d'),
                    })

        return horas_extras

    @api.model
    def work_days(self, employee, day_of_week):

        if not employee.resource_calendar_id:
            return []

        attendances = employee.resource_calendar_id.attendance_ids.filtered(
            lambda a: int(a.dayofweek) == day_of_week
        )

        info_employees = []
        for attendance in attendances:
            try:
                hour_from = datetime.strptime(f"{int(attendance.hour_from):02d}:00", "%H:%M").time()
                hour_to = datetime.strptime(f"{int(attendance.hour_to):02d}:00", "%H:%M").time()

                info_employees.append({
                    'employee_id': employee.id,
                    'hour_from': hour_from,
                    'hour_to': hour_to,
                    'day_period': getattr(attendance, 'day_period', None)
                })

            except ValueError as e:
                raise ValueError(f"Erro ao processar horários para {employee.name}: {e}")

        return info_employees


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    @api.model
    def absents(self):
        now = datetime.now()
        yesterday = fields.Date.today() - timedelta(days=1)

        employees = self.env['hr.employee'].search([])

        maputo_tz = pytz.timezone("Africa/Maputo")
        utc_tz = pytz.utc

        day_of_week = yesterday.weekday()
        work_days_data = self.work_days(day_of_week)

        attended_employees = self.env['hr.attendance'].search([
            ('check_in', '>=', yesterday),
            ('check_in', '<', fields.Date.today())
        ]).mapped('employee_id')

        absent_employees = employees - attended_employees

        leave_type = self.env['hr.leave.type'].search([('name', '=', 'Falta')], limit=1)
        if not leave_type:
            return {'error': 'Tipo de ausência "Falta" não encontrado.'}

        for emp in absent_employees:
            work_schedule = [w for w in work_days_data if w['employee_id'] == emp.id]

            if not work_schedule:
                continue

            first_shift = min(work_schedule, key=lambda x: x['hour_from'])
            last_shift = max(work_schedule, key=lambda x: x['hour_to'])

            hour_from_time = first_shift['hour_from'].time()
            hour_to_time = last_shift['hour_to'].time()

            date_from_maputo = datetime.combine(yesterday, hour_from_time)
            date_to_maputo = datetime.combine(yesterday, hour_to_time)

            date_from_maputo = maputo_tz.localize(date_from_maputo)
            date_to_maputo = maputo_tz.localize(date_to_maputo)

            date_from_utc = date_from_maputo.astimezone(utc_tz).replace(tzinfo=None)
            date_to_utc = date_to_maputo.astimezone(utc_tz).replace(tzinfo=None)

            self.env['hr.leave'].create({
                'holiday_status_id': leave_type.id,
                'employee_id': emp.id,
                'date_from': date_from_utc,
                'date_to': date_to_utc,
                'request_date_from': yesterday,
                'request_date_to': yesterday,
                'state': 'confirm',
                'number_of_days': 1,
                'duration_display': 1,
            })

        return {'success': f'{len(absent_employees)} funcionários ausentes foram lançados no Time Off.'}

    @api.model
    def work_days(self, day_of_week):
        records = self.env['hr.employee'].sudo().search([])

        info_employees = []
        for employee in records:
            attendances = employee.resource_calendar_id.attendance_ids.filtered(
                lambda a: int(a.dayofweek) == day_of_week
            )

            if not attendances:
                continue

            for attendance in attendances:
                try:
                    hour_from = datetime.strptime(f"{int(attendance.hour_from):02d}:00", "%H:%M").time()
                    hour_to = datetime.strptime(f"{int(attendance.hour_to):02d}:00", "%H:%M").time()

                    info_employees.append({
                        'employee_id': employee.id,
                        'hour_from': hour_from,
                        'hour_to': hour_to,
                    })
                except ValueError as e:
                    raise ValueError(f"Erro ao processar horários para {employee.name}: {e}")

        return info_employees
