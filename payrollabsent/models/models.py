from datetime import timedelta, datetime
from datetime import date, datetime, time
from odoo import api, fields, models, tools, _
from pytz import timezone
import babel
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payrollabsent_id = fields.Many2one('payrollabsent.payrollabsent', string='Ausências')

    def get_inputs(self, contracts, date_from, date_to):
        """
        Gera os dados de entrada para os contratos com base em atrasos, faltas e horas extras
        entre as datas fornecidas.
        """
        res = []
        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [rule_id for rule_id, _ in sorted(rule_ids, key=lambda x: x[1])]

        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

        faltas_por_funcionario = self._look_for_fouls(date_from, date_to)
        delays_info = self._daily_delays_check(date_from, date_to)
        overtime_info = self._daily_overtime_check(date_from, date_to)

        total_delays_by_employee = {}
        total_overtime_by_employee = {}

        for delay in delays_info:
            employee_id = delay['id']
            delay_minutes = delay.get('delay', 0)
            total_delays_by_employee[employee_id] = total_delays_by_employee.get(employee_id, 0) + delay_minutes

        for overtime in overtime_info:
            employee_id = overtime['id']
            overtime_minutes = overtime.get('overtime_minutes', 0)
            total_overtime_by_employee[employee_id] = total_overtime_by_employee.get(employee_id, 0) + overtime_minutes

        for contract in contracts:
            employee_id = contract.employee_id.id

            faltas = sum(1 for falta in faltas_por_funcionario if falta['id'] == employee_id)

            total_delay_minutes = total_delays_by_employee.get(employee_id, 0)
            delay_amount = round(total_delay_minutes / 60, 2)

            total_overtime_minutes = total_overtime_by_employee.get(employee_id, 0)
            overtime_amount = round(total_overtime_minutes / 60, 2)

            for input in inputs:
                input_data = self._get_input_data(input, employee_id, delay_amount, faltas, overtime_info)
                if input_data:
                    res.append(input_data)

        return res

    def _get_input_data(self, input, employee_id, delay_amount, faltas, overtime_info):
        """Auxilia na geração dos dados de entrada baseados no código do input"""
        if input.code == 'D_P_A':
            return {
                'name': input.name,
                'code': input.code,
                'amount': delay_amount,
                'contract_id': employee_id,
            }
        elif input.code == 'TO_F_D':
            return {
                'name': input.name,
                'code': input.code,
                'amount': faltas,
                'contract_id': employee_id,
            }
        elif input.code == 'H_E_150':
            overtime_until_20h = sum(
                self._convert_time_to_minutes(overtime.get('overtime_until_20h', '0 min'))
                for overtime in overtime_info if overtime['id'] == employee_id
            )
            return {
                'name': input.name,
                'code': input.code,
                'amount': overtime_until_20h / 60,
                'contract_id': employee_id,
            }
        elif input.code == 'H_E_200':
            overtime_after_20h = sum(
                self._convert_time_to_minutes(overtime.get('overtime_after_20h', '0 min'))
                for overtime in overtime_info if overtime['id'] == employee_id
            )
            return {
                'name': input.name,
                'code': input.code,
                'amount': overtime_after_20h / 60,
                'contract_id': employee_id,
            }
        else:
            return {
                'name': input.name,
                'code': input.code,
                'amount': 0,
                'contract_id': employee_id,
            }

    def _convert_time_to_minutes(self, time_str):
        """Converte uma string de tempo como '3h', '30 min', '1h 30 min' em minutos."""
        time_str = time_str.lower()
        minutes = 0

        if 'h' in time_str:
            hours = int(time_str.split('h')[0].strip())
            minutes += hours * 60

        if 'min' in time_str:
            min_part = time_str.split('min')[0].strip()
            if min_part:
                minutes += int(min_part)

        return minutes

    def _look_for_fouls(self, date_from, date_to):
        """Busca as faltas dos funcionários no intervalo de datas fornecido."""

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

    def _daily_delays_check(self, date_from, date_to):
        """Verifica atrasos dos funcionários no intervalo de datas fornecido."""
        records = self.env['hr.attendance'].sudo().search([
            ('check_in', '>=', date_from),
            ('check_in', '<=', date_to)
        ])

        delays_info = []
        for row in records:
            check_in = row.check_in
            if not check_in:
                continue

            day_of_week = check_in.weekday()
            resource_calendar = row.employee_id.resource_calendar_id

            if not resource_calendar:
                continue

            attendance = next(
                (att for att in resource_calendar.attendance_ids if int(att.dayofweek) == day_of_week),
                None
            )

            if not attendance:
                continue

            check_in_time = check_in.time()
            expected_time = (datetime.min + timedelta(hours=attendance.hour_from)).time()
            is_late = check_in_time > expected_time

            delay_minutes = 0
            if is_late:
                check_in_datetime = datetime.combine(datetime.today(), check_in_time)
                expected_datetime = datetime.combine(datetime.today(), expected_time)

                delay_delta = check_in_datetime - expected_datetime
                delay_minutes = delay_delta.total_seconds() / 60

            delays_info.append({
                'id': row.employee_id.id,
                'employee_name': row.employee_id.name,
                'check_in': check_in.strftime('%H:%M'),
                'expected_time': expected_time.strftime('%H:%M'),
                'is_late': is_late,
                'delay': delay_minutes
            })

        return delays_info

    def _daily_overtime_check(self, date_from, date_to):
        """Verifica horas extras dos funcionários no intervalo de datas fornecido."""
        employees = self.env['hr.employee'].sudo().search([])
        overtime_info = []

        for employee in employees:
            records = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '>=', date_from),
                ('check_out', '<=', date_to)
            ])

            for row in records:
                check_out = row.check_out
                if not check_out:
                    continue

                resource_calendar = row.employee_id.resource_calendar_id
                if not resource_calendar:
                    continue

                check_out_date = check_out.date()
                attendances_today = [
                    att for att in resource_calendar.attendance_ids
                    if int(att.dayofweek) == check_out_date.weekday()
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

                total_overtime_minutes = 0
                overtime_part1_str = "0 min"
                overtime_part2_str = "0 min"

                if is_overtime:
                    check_out_datetime = datetime.combine(check_out_date, check_out_time)
                    expected_datetime = datetime.combine(check_out_date, expected_time)

                    overtime_delta = check_out_datetime - expected_datetime
                    overtime_minutes = overtime_delta.total_seconds() / 60

                    expected_time_obj = datetime.combine(check_out_date, expected_time)
                    time_until_20 = datetime.combine(check_out_date, datetime.min.time()) + timedelta(hours=20)
                    overtime_until_20 = min(check_out_datetime, time_until_20) - expected_time_obj

                    overtime_until_20_minutes = max(overtime_until_20.total_seconds() / 60, 0)
                    overtime_part1_str = f"{int(overtime_until_20_minutes)} min" if overtime_until_20_minutes < 60 else f"{int(overtime_until_20_minutes // 60)}h"
                    total_overtime_minutes += overtime_until_20_minutes

                    if check_out_datetime > time_until_20:
                        overtime_after_20 = check_out_datetime - time_until_20
                        overtime_after_20_minutes = overtime_after_20.total_seconds() / 60
                        overtime_part2_str = f"{int(overtime_after_20_minutes)} min" if overtime_after_20_minutes < 60 else f"{int(overtime_after_20_minutes // 60)}h"
                        total_overtime_minutes += overtime_after_20_minutes

                overtime_info.append({
                    'id': row.employee_id.id,
                    'employee_name': row.employee_id.name,
                    'check_out': check_out.strftime('%H:%M'),
                    'expected_time': expected_time.strftime('%H:%M'),
                    'is_overtime': is_overtime,
                    'overtime_minutes': int(total_overtime_minutes),
                    'overtime_until_20h': overtime_part1_str,
                    'overtime_after_20h': overtime_part2_str
                })

        return overtime_info

class PayrollAbsent(models.Model):
    _name = 'payrollabsent.payrollabsent'
    _description = 'Payroll Absent'

    absent_date = fields.Date(string='Data da Verificação', default=fields.Date.today)
    absent_employees = fields.Many2many('hr.employee', string='Funcionários Ausentes',
                                        compute='_compute_absent_employees')
    department_id = fields.Many2one('hr.department', string='Departamento')

    payslip_ids = fields.One2many('hr.payslip', 'payrollabsent_id', string='Folhas de Pagamento')

    @api.model
    def get_week_start_date(self):
        today = fields.Date.context_today(self)
        week_start = today - timedelta(days=7)
        return week_start

    @api.depends('absent_date')
    def _compute_absent_employees(self):
        for record in self:
            check_date = record.absent_date
            all_employees = self.env['hr.employee'].search([])

            check_date_str = check_date.strftime('%Y-%m-%d')

            start_datetime = f"{check_date_str} 00:00:00"
            end_datetime = f"{check_date_str} 23:59:59"

            attendance_checkins = self.env['hr.attendance'].search([
                ('check_in', '>=', start_datetime),
                ('check_in', '<=', end_datetime)
            ])

            checked_in_employee_ids = attendance_checkins.mapped('employee_id.id')

            absent_employees = all_employees.filtered(lambda e: e.id not in checked_in_employee_ids)
            record.absent_employees = absent_employees

    @api.model
    def ausentes(self, _logger=None):
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        current_weekday = now.weekday()

        if current_weekday == 6:  # Domingo
            _logger.info("O método 'ausentes' não foi acionado. Hoje é domingo, não há trabalho.")
            return

        if current_weekday == 0:

            date_to_check = now - timedelta(days=2)
        else:

            date_to_check = now - timedelta(days=1)

        if current_hour == 0 and current_minute == 0:
            holiday_status = self.env['hr.leave.type'].sudo().search([('name', '=', 'Falta')], limit=1)
            if not holiday_status:
                print("Não foi encontrado um status de férias com o nome 'Falta'.")

                return

            employees = self.env['hr.employee'].sudo().search([])
            for employee in employees:

                attendances = self.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', date_to_check.replace(hour=0, minute=0, second=0)),
                    ('check_in', '<=', date_to_check.replace(hour=23, minute=59, second=59))
                ], limit=1)

                if not attendances:
                    self.env['hr.leave'].sudo().create({
                        'holiday_status_id': holiday_status.id,
                        'employee_id': employee.id,
                        'date_from': date_to_check,
                        'date_to': date_to_check,
                        'request_date_from': date_to_check,
                        'request_date_to': date_to_check,
                        'number_of_days': 1.0,
                        'duration_display': 1.0,
                    })

                    print("Falta registrada para o funcionário %s (ID: %s) no dia %s.",
                                 employee.name, employee.id, date_to_check.date())
                else:

                    print("Funcionário %s (ID: %s) presente no dia %s (check-in encontrado).",
                                 employee.name, employee.id, date_to_check.date())
        else:

            print("O método 'ausentes' não foi acionado fora do horário programado. Hora atual: %s.", now)



