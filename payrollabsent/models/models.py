# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
from datetime import date, datetime, time
from odoo import api, fields, models, tools, _
from pytz import timezone
import babel


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payrollabsent_id = fields.Many2one('payrollabsent.payrollabsent', string='Ausências')

    def compute_sheet(self):

        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                           self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in self._get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines, 'number': number})
        return True

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []

        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from), time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to), time.max)

            leaves = {}
            calendar = contract.resource_calendar_id
            tz = timezone(calendar.tz)
            day_leave_intervals = contract.employee_id.list_leaves(day_from, day_to,
                                                                   calendar=contract.resource_calendar_id)
            for day, hours, leave in day_leave_intervals:
                holiday = leave.holiday_id
                print(f"Holiday ID: {holiday.holiday_status_id}")
                current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
                    'name': holiday.holiday_status_id.name or _('Global Leaves'),
                    'sequence': 5,
                    'code': holiday.holiday_status_id.code or 'GLOBAL',
                    'number_of_days': 0.0,
                    'number_of_hours': 0.0,
                    'contract_id': contract.id,
                })
                current_leave_struct['number_of_hours'] += hours
                work_hours = calendar.get_work_hours_count(
                    tz.localize(datetime.combine(day, time.min)),
                    tz.localize(datetime.combine(day, time.max)),
                    compute_leaves=False,
                )
                if work_hours:
                    current_leave_struct['number_of_days'] += hours / work_hours

            work_data = contract.employee_id.get_work_days_data(day_from, day_to,
                                                                calendar=contract.resource_calendar_id)
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': work_data['days'],
                'number_of_hours': work_data['hours'],
                'contract_id': contract.id,
            }

            print(f"Attending data for contract {contract.id}: {attendances}")

            res.append(attendances)
            res.extend(leaves.values())

        return res

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = []

        structure_ids = contracts.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]

        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

        faltas_por_funcionario = self.look_for_fouls()

        print(f"Inputs kkkkkkkkkkkk: {inputs}")

        for contract in contracts:
            faltas = sum(1 for falta in faltas_por_funcionario if falta['id'] == contract.employee_id.id)

            for input in inputs:
                if input.code == 'TO_F_D':
                    input_data = {
                        'name': input.name,
                        'code': input.code,
                        'amount': faltas,
                        'contract_id': contract.id,
                    }
                else:
                    input_data = {
                        'name': input.name,
                        'code': input.code,
                        'amount': 0,
                        'contract_id': contract.id,
                    }

                res.append(input_data)

        print(f"Input Line Data kkkkkkk: {res}")
        return res

    def look_for_fouls(self):

        busca = self.env['hr.leave'].sudo().search([])
        dados = []
        for dado in busca:
            dados.append({
                'id': dado.employee_id.id,
                'name': dado.employee_id.name,
                'date_from': dado.date_from.strftime('%Y-%m-%d'),
                'date_to': dado.date_to.strftime('%Y-%m-%d'),
            })
        return dados

    def daily_delays_check(self):
        records = self.env['hr.attendance'].sudo().search([])

        delays_info = []

        for row in records:
            check_in = row.check_in
            if not check_in:
                continue
            day_of_week = check_in.weekday()

            resource_calendar = row.row.employee_id.resource_calendar_id
            if not resource_calendar:
                continue

            attendance = next(
                (att for att in resource_calendar.attendance_ids if int(att.dayofweek) == day_of_week),
                None
            )

            if not attendance:
                continue

            check_in_time = check_in.time()
            expected_time =(datetime.min + timedelta(hours=attendance.hour_from)).time()

            is_late = check_in_time > expected_time

            delays_info.append({
                'id': row.id,
                'employee_name': row.employee_id.name,
                'check_in': check_in.strftime('%H:%M'),
                'expected_time': expected_time.strftime('%H:%M'),
                'is_late': is_late
            })



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
    def ausentes(self):
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        if current_hour == 7 and current_minute == 50:
            print(f"[INFO] O método 'ausentes' foi acionado em {now}. Verificando ausências...")

            employees = self.env['hr.employee'].sudo().search([('id', '=', '20')])
            for employee in employees:
                attendance = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '!=', False)
                ], limit=1)

                if not attendance:
                    print(f"[INFO] Funcionário {employee.name} ausente (sem check-in). Criando registro de ausência...")

                    self.env['hr.leave'].sudo().create({
                        'holiday_status_id': 7,
                        'employee_id': employee.id,
                        'date_from': now,
                        'date_to': now,
                        'request_date_from': now,
                        'request_date_to': now,
                        'number_of_days': 1.0,
                        'duration_display': 1.0,
                    })

                    print(f"[INFO] Ausência registrada para o funcionário {employee.name}.")
                else:
                    print(f"[INFO] Funcionário {employee.name} presente (check-in encontrado).")
        else:
            print(f"[INFO] O método 'ausentes' não foi acionado {current_hour} e {current_minute}. Hora atual: {now}.")
