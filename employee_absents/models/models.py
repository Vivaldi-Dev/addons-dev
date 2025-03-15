# -*- coding: utf-8 -*-
from datetime import timedelta, datetime, date

import pytz
from pytz import timezone, UTC

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


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
                        extra['minutes_extra'] for extra in overtimes if
                        extra['id'] == contract.employee_id.id and extra['tipo'] == 'H_E_150'
                    )
                    input_data['amount'] = round(total_extras / 60, 2)

                if input.code == "H_E_200":
                    total_extras = sum(
                        extra['minutes_extra'] for extra in overtimes if
                        extra['id'] == contract.employee_id.id and extra['tipo'] == 'H_E_200'
                    )
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

        return atrasos

    def _look_for_overtime(self, date_from, date_to):


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

            work_day = self.work_days(employee, day_of_week)

            expected_time = work_day.get('hour_to')


            if expected_time and check_out_time > expected_time:

                limite_h_e_150 = datetime.strptime("20:00", "%H:%M").time()

                if check_out_time > limite_h_e_150:
                    overtime_seconds_h_e_150 = (datetime.combine(date.today(), limite_h_e_150) -
                                                datetime.combine(date.today(), expected_time)).total_seconds()
                else:
                    overtime_seconds_h_e_150 = (datetime.combine(date.today(), check_out_time) -
                                                datetime.combine(date.today(), expected_time)).total_seconds()

                overtime_minutes_h_e_150 = overtime_seconds_h_e_150 / 60

                if check_out_time > limite_h_e_150:
                    overtime_seconds_h_e_200 = (datetime.combine(date.today(), check_out_time) -
                                                datetime.combine(date.today(), limite_h_e_150)).total_seconds()
                    overtime_minutes_h_e_200 = overtime_seconds_h_e_200 / 60
                else:
                    overtime_minutes_h_e_200 = 0

                print(f"✅ Horas Extras H_E_150: {int(overtime_minutes_h_e_150)} minutos")
                print(f"✅ Horas Extras H_E_200: {int(overtime_minutes_h_e_200)} minutos\n")

                if overtime_minutes_h_e_150 > 0:
                    horas_extras.append({
                        'id': employee.id,
                        'name': employee.name,
                        'minutes_extra': int(overtime_minutes_h_e_150),
                        'date': check_out_local.strftime('%Y-%m-%d'),
                        'tipo': 'H_E_150',
                    })

                if overtime_minutes_h_e_200 > 0:
                    horas_extras.append({
                        'id': employee.id,
                        'name': employee.name,
                        'minutes_extra': int(overtime_minutes_h_e_200),
                        'date': check_out_local.strftime('%Y-%m-%d'),
                        'tipo': 'H_E_200',
                    })
            else:
                print("O funcionário saiu antes do horário esperado. Nenhuma hora extra.\n")

        return horas_extras

    @api.model
    def work_days(self, employee, day_of_week):
        """Retorna os horários de trabalho do funcionário para um dia da semana específico."""

        if not employee.resource_calendar_id:
            return None  # Retorna None se não houver calendário definido

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


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    @api.model
    def absents(self):
        """
        Método para cron job que registra faltas dos funcionários que não registraram presença no dia anterior.
        Funciona para todas as empresas.
        """
        now = datetime.now()
        yesterday = fields.Date.today() - timedelta(days=1)

        maputo_tz = pytz.timezone("Africa/Maputo")
        utc_tz = pytz.utc

        day_of_week = yesterday.weekday()

        companies = self.env['res.company'].search([])
        for company in companies:

            employees = self.env['hr.employee'].search([('company_id', '=', company.id)])

            attended_employees = self.env['hr.attendance'].search([
                ('employee_id.company_id', '=', company.id),
                ('check_in', '>=', yesterday),
                ('check_in', '<', fields.Date.today())
            ]).mapped('employee_id')

            absent_employees = employees - attended_employees

            leave_type = self.env['hr.leave.type'].search([
                ('name', '=', 'Falta'),
                ('company_id', '=', company.id)
            ], limit=1)

            if not leave_type:
                print(f'Tipo de ausência "Falta" não encontrado para a empresa {company.name}.')
                continue

            for emp in absent_employees:

                work_schedule = self.work_days(emp.resource_calendar_id, day_ofweek=day_of_week)

                if not work_schedule:
                    continue

                first_shift = min(work_schedule, key=lambda x: x['hour_from'])
                last_shift = max(work_schedule, key=lambda x: x['hour_to'])

                hour_from_time = first_shift['hour_from']
                hour_to_time = last_shift['hour_to']

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

        return {'success': 'Faltas registradas para todas as empresas.'}

    @api.model
    def work_days(self, resource_calendar, day_ofweek):
        """
        Retorna os horários de trabalho de um funcionário para um determinado dia da semana.
        """
        if not resource_calendar:
            return []

        attendances = resource_calendar.attendance_ids.filtered(
            lambda a: int(a.dayofweek) == day_ofweek
        )

        work_schedule = []
        for attendance in attendances:
            try:
                hour_from = datetime.strptime(f"{int(attendance.hour_from):02d}:00", "%H:%M").time()
                hour_to = datetime.strptime(f"{int(attendance.hour_to):02d}:00", "%H:%M").time()

                work_schedule.append({
                    'hour_from': hour_from,
                    'hour_to': hour_to,
                })
            except ValueError as e:
                raise ValueError(f"Erro ao processar horários: {e}")

        return work_schedule
