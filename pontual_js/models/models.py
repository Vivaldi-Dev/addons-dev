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
        employees = self.env['hr.employee'].sudo().search([
            ('company_id', '=', company_id),
            ('active', '=', True)
        ])
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

        faltas_por_dia = self._look_for_fouls(start_date, end_date, company_id)

        return {
            'total_presents': len(presents),
            'present_list': presents,
            'total_absents': len(absents),
            'absent_list': absents,
            'total_atrasos': total_atrasos,
            'atrasos_list': atrasos,
            'faltas_por_dia': list(faltas_por_dia.values()),
        }

    def _look_for_fouls(self, start_date, end_date, company_id):
        """Busca faltas por empresa e retorna o total de faltas por dia da semana."""


        print(start_date, end_date, company_id)

        busca = self.env['hr.leave'].sudo().search([
            ('date_from', '>=', start_date),
            ('date_to', '<=', end_date),
            ('state', 'in', ['confirm', 'refuse']),
            ('employee_id.company_id', '=', company_id),
        ])

       
        faltas_por_dia = {
            0: 0,  # Segunda
            1: 0,  # Terça
            2: 0,  # Quarta
            3: 0,  # Quinta
            4: 0,  # Sexta
            5: 0,  # Sábado
            6: 0,  # Domingo
        }

        for dado in busca:
            date_from = fields.Datetime.from_string(dado.date_from)
            date_to = fields.Datetime.from_string(dado.date_to)

            # Itera sobre cada dia no intervalo da falta
            current_date = date_from
            while current_date <= date_to:
                dia_semana = current_date.weekday()  # 0 = Segunda, 6 = Domingo
                faltas_por_dia[dia_semana] += 1
                current_date += timedelta(days=1)

        dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        print("\n=== FALTAS POR DIA DA SEMANA ===")
        for dia, total in faltas_por_dia.items():
            print(f"{dias_semana[dia]}: {total} faltas")

        return faltas_por_dia

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

        return atrasos

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

    def look_for_fouls(self,start_date, end_date, company_id):
        employees = self.env['hr.employee'].sudo().search([('company_id', '=', int(company_id))])
        total_employees = len(employees)



