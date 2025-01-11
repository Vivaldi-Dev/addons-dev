# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import date, datetime, time
from datetime import timedelta
import babel

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('struct_id')
    def _onchange_struct_id(self):
        """
        Atualiza os inputs sempre que a estrutura salarial for alterada, chamando
        o método _get_input_data para gerar os dados de entrada.
        """
        res = []
        self.input_line_ids = [(5, 0, 0)]

        if self.struct_id:

            rule_ids = self.env['hr.payroll.structure'].browse(self.struct_id.id).get_all_rules()
            sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
            inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

            contracts = self.contract_id
            date_from = self.date_from
            date_to = self.date_to

            faltas_por_funcionario = self._look_for_fouls(date_from, date_to)
            delays_info = self._daily_delays_check(date_from, date_to)
            overtime_info = self._daily_overtime_check(date_from, date_to)

            for input in inputs:
                employee_id = self.contract_id.employee_id.id

                faltas = sum(1 for falta in faltas_por_funcionario if falta['id'] == employee_id)
                total_delay_minutes = sum(delay.get('delay', 0) for delay in delays_info if delay['id'] == employee_id)
                delay_amount = round(total_delay_minutes / 60, 2)

                total_overtime_minutes = sum(
                    overtime.get('overtime_minutes', 0) for overtime in overtime_info if overtime['id'] == employee_id)
                overtime_amount = round(total_overtime_minutes / 60, 2)

                input_data = self._get_input_data(input, employee_id, delay_amount, faltas, overtime_info)

                if input_data:
                    res.append((0, 0, input_data))

        self.input_line_ids = res

    def _get_input_data(self, input, employee_id, delay_amount, faltas, overtime_info):
        """Auxilia na geração dos dados de entrada baseados no código do input"""
        if input.code == 'D_P_A':
            return {
                'name': input.name,
                'code': input.code,
                'amount': delay_amount,
                'contract_id': self.contract_id.id,  # Aqui usaremos o contract_id
            }
        elif input.code == 'TO_F_D':
            return {
                'name': input.name,
                'code': input.code,
                'amount': faltas,
                'contract_id': self.contract_id.id,  # Aqui usaremos o contract_id
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
                'contract_id': self.contract_id.id,  # Aqui usaremos o contract_id
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
                'contract_id': self.contract_id.id,  # Aqui usaremos o contract_id
            }
        else:
            return {
                'name': input.name,
                'code': input.code,
                'amount': 0,
                'contract_id': self.contract_id.id,  # Aqui usaremos o contract_id
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


