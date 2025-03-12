from odoo import models, fields, api
from datetime import timedelta, datetime, date
import pytz
from pytz import timezone, UTC
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('struct_id')
    def _onchange_struct_id(self):


        self.input_line_ids = [(5, 0, 0)]

        if self.struct_id and self.contract_id:

            inputs = self._get_inputs_for_structure(self.struct_id, self.contract_id, self.date_from, self.date_to)


            self.input_line_ids = [(0, 0, input_data) for input_data in inputs]

    def _get_inputs_for_structure(self, struct_id, contract, date_from, date_to):

        res = []


        rule_ids = struct_id.get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

        fouls = self._look_for_fouls(date_from, date_to)
        attendances = self._look_for_late_arrivals(date_from, date_to)
        overtimes = self._look_for_overtime(date_from, date_to)

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

            elif input.code == "D_P_A":
                employee_id = int(contract.employee_id.id)
                total_atrasos = sum(
                    atraso['minutes_late'] for atraso in attendances if int(atraso['id']) == employee_id
                )
                input_data['amount'] = total_atrasos / 60

            elif input.code == "H_E_150":
                total_extras = sum(
                    extra['minutes_extra'] for extra in overtimes if
                    extra['id'] == contract.employee_id.id and extra['tipo'] == 'H_E_150'
                )
                input_data['amount'] = round(total_extras / 60, 2)

            elif input.code == "H_E_200":  # Horas extras 200%
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

        return [{
            'id': dado.employee_id.id,
            'name': dado.employee_id.name,
            'date_from': dado.date_from.strftime('%Y-%m-%d'),
            'date_to': dado.date_to.strftime('%Y-%m-%d'),
        } for dado in busca]

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

        return horas_extras

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