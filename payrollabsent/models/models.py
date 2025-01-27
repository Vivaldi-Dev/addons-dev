from datetime import timedelta, datetime
from datetime import date, datetime, time
from odoo import api, fields, models, tools, _
from pytz import timezone
import babel
import logging
from pytz import timezone
from datetime import datetime, timedelta
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

MAPUTO_TZ = timezone('Africa/Maputo')

# class HrPayslip(models.Model):
#     _inherit = 'hr.payslip'
#
#     payrollabsent_id = fields.Many2one('payrollabsent.payrollabsent', string='Ausências')
#
#     def get_inputs(self, contracts, date_from, date_to):
#         """
#         Gera os dados de entrada para os contratos com base em atrasos, faltas e horas extras
#         entre as datas fornecidas.
#         """
#         res = []
#         structure_ids = contracts.get_all_structures()
#         rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
#         sorted_rule_ids = [rule_id for rule_id, _ in sorted(rule_ids, key=lambda x: x[1])]
#
#         inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')
#
#         faltas_por_funcionario = self._look_for_fouls(date_from, date_to)
#         delays_info = self._daily_delays_check(date_from, date_to)
#         overtime_info = self._daily_overtime_check(date_from, date_to)
#
#         total_delays_by_employee = {}
#         total_overtime_by_employee = {}
#
#         for delay in delays_info:
#             employee_id = delay['id']
#             delay_minutes = delay.get('delay', 0)
#             total_delays_by_employee[employee_id] = total_delays_by_employee.get(employee_id, 0) + delay_minutes
#
#         for overtime in overtime_info:
#             employee_id = overtime['id']
#             overtime_minutes = overtime.get('overtime_minutes', 0)
#             total_overtime_by_employee[employee_id] = total_overtime_by_employee.get(employee_id, 0) + overtime_minutes
#
#         for contract in contracts:
#             employee_id = contract.employee_id.id
#
#             faltas = sum(1 for falta in faltas_por_funcionario if falta['id'] == employee_id)
#
#             total_delay_minutes = total_delays_by_employee.get(employee_id, 0)
#             delay_amount = round(total_delay_minutes / 60, 2)
#
#             total_overtime_minutes = total_overtime_by_employee.get(employee_id, 0)
#             overtime_amount = round(total_overtime_minutes / 60, 2)
#
#             for input in inputs:
#                 input_data = self._get_input_data(input, employee_id, delay_amount, faltas, overtime_info)
#                 if input_data:
#                     res.append(input_data)
#
#         return res
#
#     def _get_input_data(self, input, employee_id, delay_amount, faltas, overtime_info):
#         """Auxilia na geração dos dados de entrada baseados no código do input"""
#         if input.code == 'D_P_A':
#             return {
#                 'name': input.name,
#                 'code': input.code,
#                 'amount': delay_amount,
#                 'contract_id': employee_id,
#             }
#         elif input.code == 'TO_F_D':
#             return {
#                 'name': input.name,
#                 'code': input.code,
#                 'amount': faltas,
#                 'contract_id': employee_id,
#             }
#         elif input.code == 'H_E_150':
#             overtime_until_20h = sum(
#                 self._convert_time_to_minutes(overtime.get('overtime_until_20h', '0 min'))
#                 for overtime in overtime_info if overtime['id'] == employee_id
#             )
#             return {
#                 'name': input.name,
#                 'code': input.code,
#                 'amount': overtime_until_20h / 60,
#                 'contract_id': employee_id,
#             }
#         elif input.code == 'H_E_200':
#             overtime_after_20h = sum(
#                 self._convert_time_to_minutes(overtime.get('overtime_after_20h', '0 min'))
#                 for overtime in overtime_info if overtime['id'] == employee_id
#             )
#             return {
#                 'name': input.name,
#                 'code': input.code,
#                 'amount': overtime_after_20h / 60,
#                 'contract_id': employee_id,
#             }
#         else:
#             return {
#                 'name': input.name,
#                 'code': input.code,
#                 'amount': 0,
#                 'contract_id': employee_id,
#             }
#
#     def _convert_time_to_minutes(self, time_str):
#         """Converte uma string de tempo como '3h', '30 min', '1h 30 min' em minutos."""
#         time_str = time_str.lower()
#         minutes = 0
#
#         if 'h' in time_str:
#             hours = int(time_str.split('h')[0].strip())
#             minutes += hours * 60
#
#         if 'min' in time_str:
#             min_part = time_str.split('min')[0].strip()
#             if min_part:
#                 minutes += int(min_part)
#
#         return minutes
#
#     def _look_for_fouls(self, date_from, date_to):
#         """Busca as faltas dos funcionários no intervalo de datas fornecido."""
#
#         busca = self.env['hr.leave'].sudo().search([
#             ('date_from', '>=', date_from),
#             ('date_to', '<=', date_to),
#             ('state', 'in', ['confirm', 'refuse']),
#         ])
#
#         dados = []
#         for dado in busca:
#             dados.append({
#                 'id': dado.employee_id.id,
#                 'name': dado.employee_id.name,
#                 'date_from': dado.date_from.strftime('%Y-%m-%d'),
#                 'date_to': dado.date_to.strftime('%Y-%m-%d'),
#             })
#
#         return dados
#
#     def _daily_delays_check(self, date_from, date_to):
#         """Verifica atrasos dos funcionários no intervalo de datas fornecido."""
#         records = self.env['hr.attendance'].sudo().search([
#             ('check_in', '>=', date_from),
#             ('check_in', '<=', date_to)
#         ])
#
#         delays_info = []
#         for row in records:
#             check_in = row.check_in
#             if not check_in:
#                 continue
#
#             day_of_week = check_in.weekday()
#             resource_calendar = row.employee_id.resource_calendar_id
#
#             if not resource_calendar:
#                 continue
#
#             attendance = next(
#                 (att for att in resource_calendar.attendance_ids if int(att.dayofweek) == day_of_week),
#                 None
#             )
#
#             if not attendance:
#                 continue
#
#             check_in_time = check_in.time()
#             expected_time = (datetime.min + timedelta(hours=attendance.hour_from)).time()
#             is_late = check_in_time > expected_time
#
#             delay_minutes = 0
#             if is_late:
#                 check_in_datetime = datetime.combine(datetime.today(), check_in_time)
#                 expected_datetime = datetime.combine(datetime.today(), expected_time)
#
#                 delay_delta = check_in_datetime - expected_datetime
#                 delay_minutes = delay_delta.total_seconds() / 60
#
#             delays_info.append({
#                 'id': row.employee_id.id,
#                 'employee_name': row.employee_id.name,
#                 'check_in': check_in.strftime('%H:%M'),
#                 'expected_time': expected_time.strftime('%H:%M'),
#                 'is_late': is_late,
#                 'delay': delay_minutes
#             })
#
#         return delays_info
#
#     def _daily_overtime_check(self, date_from, date_to):
#         """Verifica horas extras dos funcionários no intervalo de datas fornecido."""
#         employees = self.env['hr.employee'].sudo().search([])
#         overtime_info = []
#
#         for employee in employees:
#             records = self.env['hr.attendance'].sudo().search([
#                 ('employee_id', '=', employee.id),
#                 ('check_out', '>=', date_from),
#                 ('check_out', '<=', date_to)
#             ])
#
#             for row in records:
#                 check_out = row.check_out
#                 if not check_out:
#                     continue
#
#                 resource_calendar = row.employee_id.resource_calendar_id
#                 if not resource_calendar:
#                     continue
#
#                 check_out_date = check_out.date()
#                 attendances_today = [
#                     att for att in resource_calendar.attendance_ids
#                     if int(att.dayofweek) == check_out_date.weekday()
#                 ]
#
#                 if not attendances_today:
#                     continue
#
#                 afternoon_attendance = next(
#                     (att for att in attendances_today if att.hour_from >= 12),
#                     None
#                 )
#                 attendance = afternoon_attendance or attendances_today[0]
#
#                 expected_time = (datetime.min + timedelta(hours=attendance.hour_to)).time()
#
#                 check_out_time = check_out.time()
#
#                 is_overtime = check_out_time > expected_time
#
#                 total_overtime_minutes = 0
#                 overtime_part1_str = "0 min"
#                 overtime_part2_str = "0 min"
#
#                 if is_overtime:
#                     check_out_datetime = datetime.combine(check_out_date, check_out_time)
#                     expected_datetime = datetime.combine(check_out_date, expected_time)
#
#                     overtime_delta = check_out_datetime - expected_datetime
#                     overtime_minutes = overtime_delta.total_seconds() / 60
#
#                     expected_time_obj = datetime.combine(check_out_date, expected_time)
#                     time_until_20 = datetime.combine(check_out_date, datetime.min.time()) + timedelta(hours=20)
#                     overtime_until_20 = min(check_out_datetime, time_until_20) - expected_time_obj
#
#                     overtime_until_20_minutes = max(overtime_until_20.total_seconds() / 60, 0)
#                     overtime_part1_str = f"{int(overtime_until_20_minutes)} min" if overtime_until_20_minutes < 60 else f"{int(overtime_until_20_minutes // 60)}h"
#                     total_overtime_minutes += overtime_until_20_minutes
#
#                     if check_out_datetime > time_until_20:
#                         overtime_after_20 = check_out_datetime - time_until_20
#                         overtime_after_20_minutes = overtime_after_20.total_seconds() / 60
#                         overtime_part2_str = f"{int(overtime_after_20_minutes)} min" if overtime_after_20_minutes < 60 else f"{int(overtime_after_20_minutes // 60)}h"
#                         total_overtime_minutes += overtime_after_20_minutes
#
#                 overtime_info.append({
#                     'id': row.employee_id.id,
#                     'employee_name': row.employee_id.name,
#                     'check_out': check_out.strftime('%H:%M'),
#                     'expected_time': expected_time.strftime('%H:%M'),
#                     'is_overtime': is_overtime,
#                     'overtime_minutes': int(total_overtime_minutes),
#                     'overtime_until_20h': overtime_part1_str,
#                     'overtime_after_20h': overtime_part2_str
#                 })
#
#         return overtime_info


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    @api.model
    def ausentes(self, _logger=None):
        now = datetime.now()
        date_to_check = now - timedelta(days=1)
        date_to_check_date = date_to_check.date()

        day_of_week = date_to_check.weekday()
        work_days_data = self.work_days(day_of_week)

        companies = self.env['res.company'].sudo().search([])
        for company in companies:

            company_work_days_data = [
                data for data in work_days_data if
                self.env['hr.employee'].sudo().browse(data['employee_id']).company_id.id == company.id and
                self.env['hr.employee'].sudo().browse(data['employee_id']).device_id
            ]

            holiday_status = self.env['hr.leave.type'].sudo().search([
                ('name', '=', 'Falta'),
                ('company_id', '=', company.id)
            ], limit=1)

            if not holiday_status:
                if _logger:
                    _logger.warning(
                        "Tipo de ausência 'Falta' não encontrado para a companhia %s.",
                        company.name
                    )
                continue

            for employee_data in company_work_days_data:
                employee_id = employee_data['employee_id']
                hour_from = employee_data['hour_from']
                hour_to = employee_data['hour_to']

                hour_from_hour = hour_from.hour
                hour_from_minute = hour_from.minute
                hour_to_hour = hour_to.hour
                hour_to_minute = hour_to.minute

                date_to_check_start = date_to_check.replace(
                    hour=hour_from_hour, minute=hour_from_minute
                )
                date_to_check_end = date_to_check.replace(
                    hour=hour_to_hour, minute=hour_to_minute
                )

                employee = self.env['hr.employee'].sudo().search([
                    ('id', '=', employee_id),
                    ('company_id', '=', company.id)
                ], limit=1)

                if not employee:
                    if _logger:
                        _logger.warning(
                            "Funcionário %s não pertence à companhia %s.",
                            employee_id, company.name
                        )
                    continue

                attendances = self.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '<=', date_to_check_date + timedelta(days=1)),
                    ('check_out', '>=', date_to_check_date),
                ], limit=1)

                overlapping_leave = self.env['hr.leave'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', holiday_status.id),
                    '|',
                    ('request_date_from', '<=', date_to_check_date),
                    ('request_date_to', '>=', date_to_check_date),
                ], limit=1)

                if attendances or overlapping_leave:
                    if _logger:
                        _logger.info(
                            "Funcionário %s já possui ausência ou presença registrada para o dia %s.",
                            employee.name, date_to_check_date
                        )
                    continue

                self.env['hr.leave'].sudo().create({
                    'holiday_status_id': holiday_status.id,
                    'employee_id': employee.id,
                    'date_from': date_to_check_start,
                    'date_to': date_to_check_end,
                    'request_date_from': date_to_check_date,
                    'state': 'confirm',
                    'request_date_to': date_to_check_date,
                    'number_of_days': 1.0,
                    'duration_display': 1.0,
                })
                if _logger:
                    _logger.info(
                        "Ausência criada para o funcionário %s no dia %s.",
                        employee.name, date_to_check_date
                    )

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

            morning_from = None
            morning_to = None
            afternoon_from = None
            afternoon_to = None

            for attendance in attendances:
                if attendance.day_period == 'morning':
                    morning_from = attendance.hour_from
                    morning_to = attendance.hour_to
                elif attendance.day_period == 'afternoon':
                    afternoon_from = attendance.hour_from
                    afternoon_to = attendance.hour_to

            if morning_from and morning_to:
                try:
                    datetime_morning_from = datetime.strptime(f"{int(morning_from):02d}:00", "%H:%M")
                    datetime_morning_to = datetime.strptime(f"{int(morning_to):02d}:00", "%H:%M")
                    info_employees.append({
                        'employee_id': employee.id,
                        'hour_from': datetime_morning_from,
                        'hour_to': datetime_morning_to,
                    })
                except ValueError as e:
                    raise ValueError(f"Erro ao processar horários de manhã para o funcionário {employee.name}: {e}")

            if afternoon_from and afternoon_to:
                try:
                    datetime_afternoon_from = datetime.strptime(f"{int(afternoon_from):02d}:00", "%H:%M")
                    datetime_afternoon_to = datetime.strptime(f"{int(afternoon_to):02d}:00", "%H:%M")
                    info_employees.append({
                        'employee_id': employee.id,
                        'hour_from': datetime_afternoon_from,
                        'hour_to': datetime_afternoon_to,
                    })
                except ValueError as e:
                    raise ValueError(f"Erro ao processar horários da tarde para o funcionário {employee.name}: {e}")

        return info_employees

    @api.constrains('date_from', 'date_to', 'employee_id')
    def _check_date(self):
        if self.env.context.get('leave_skip_date_check', False):
            return
        for holiday in self.filtered('employee_id'):
            domain = [
                ('date_from', '<', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('employee_id', '=', holiday.employee_id.id),
                ('id', '!=', holiday.id),
                ('state', 'not in', ['cancel', 'refuse', 'confirm']),
            ]
            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(
                    _('You can not set 2 time off that overlaps on the same day for the same employee.') + '\n- %s' % (
                        holiday.display_name))
