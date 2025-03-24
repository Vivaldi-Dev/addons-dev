# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta, datetime, date

from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from datetime import datetime, date
from odoo import models, fields, api
import pytz


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    status = fields.Integer(string="Status", compute="_compute_color", store=True)
    delay_minutes = fields.Integer(string="Delay Minutes", compute="_compute_color", store=True)
    delay_duration = fields.Char(string="Delay Duration", compute="_compute_color", store=True)

    name = fields.Char(string="Reason")

    @api.onchange('employee_id')
    def _onchange_employee(self):
        print(f"Funcionário alterado para: {self.employee_id.name if self.employee_id else 'Nenhum'}")

        if self.employee_id:
            self._compute_color()

    @api.depends('check_in', 'employee_id', 'employee_id.resource_calendar_id')
    def _compute_color(self):
        for attendance in self:
            print(f"Recalculando atraso para: {attendance.employee_id.name if attendance.employee_id else 'Nenhum'}")
            if attendance.check_in:
                delay, minutes = self._check_for_delay(attendance)
                attendance.status = 4 if delay else 10
                attendance.delay_minutes = minutes if delay else 0
                attendance.delay_duration = self._format_delay_duration(minutes) if delay else "00:00"
            else:
                attendance.status = 10
                attendance.delay_minutes = 0
                attendance.delay_duration = "00:00"

    def _format_delay_duration(self, minutes):
        """
        Formata os minutos de atraso no formato HH:MM.
        Exemplo: 248 minutos → "04:08"
        """
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours:02d}:{remaining_minutes:02d}"

    def _check_for_delay(self, attendance):
        employee = attendance.employee_id
        check_in_utc = attendance.check_in

        if isinstance(check_in_utc, str):
            check_in_utc = datetime.strptime(check_in_utc, DEFAULT_SERVER_DATETIME_FORMAT)

        maputo_tz = pytz.timezone('Africa/Maputo')

        check_in_local = pytz.utc.localize(check_in_utc).astimezone(maputo_tz)
        check_in_time = check_in_local.time()

        day_of_week = check_in_local.weekday()

        work_day = self.work_days(employee, day_of_week)

        if work_day and work_day['employee_id'] == employee.id:
            expected_time = work_day['hour_from']

            if expected_time:  # Verifica se expected_time não é None
                expected_datetime = datetime.combine(check_in_local.date(), expected_time)
                expected_datetime = maputo_tz.localize(expected_datetime)

                tolerance_datetime = expected_datetime + timedelta(minutes=10)

                if check_in_local > tolerance_datetime:
                    delay = check_in_local - expected_datetime
                    delay_minutes = int(delay.total_seconds() // 60)

                    delay_hours = delay_minutes // 60
                    delay_remaining_minutes = delay_minutes % 60

                    return True, delay_minutes
            else:
                # Se expected_time for None, não há horário esperado, portanto, não há atraso
                return False, 0

        return False, 0

    @api.model
    def work_days(self, employee, day_of_week):
        """
        Retorna o horário de trabalho do funcionário para o dia da semana especificado.
        """
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
                hour_from = datetime.strptime(
                    f"{int(attendance.hour_from):02d}:{int((attendance.hour_from % 1) * 60):02d}", "%H:%M").time()
                hour_to = datetime.strptime(f"{int(attendance.hour_to):02d}:{int((attendance.hour_to % 1) * 60):02d}",
                                            "%H:%M").time()

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


class DashboardPontual(models.Model):
    _name = 'dashboard_pontual.dashboard_pontual'
    _description = 'Dashboard de Pontualidade'

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

                if expected_time:
                    expected_datetime = datetime.combine(check_in_local.date(), expected_time)
                    expected_datetime = timezone.localize(expected_datetime)

                    tolerance_datetime = expected_datetime + timedelta(minutes=10)

                    if check_in_local > tolerance_datetime:
                        delay = check_in_local - expected_datetime
                        delay_minutes = int(delay.total_seconds() // 60)

                        atrasos.append({
                            'id': employee.id,
                            'name': employee.name,
                            'minutes_late': delay_minutes,
                            'date': check_in_local.strftime('%Y-%m-%d'),
                        })
                else:

                    continue

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


class HrAbsentEmployees(models.TransientModel):
    _name = 'absent.employees'
    _description = 'Funcionários sem Check-in'

    employee_ids = fields.One2many('hr.employee', string="Funcionário", compute="_funcionarios", store=False)

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        readonly=True,
        copy=False,
        help="Empresa",
        default=lambda self: self.env.company
    )


class HrAbsentEmployees(models.TransientModel):
    _name = 'absent.employees'
    _description = 'Funcionários sem Check-in'

    employee_ids = fields.Many2many(
        'hr.employee',
        string="Funcionários Ausentes",
        compute="_compute_funcionarios",
        store=False
    )

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        readonly=True,
        default=lambda self: self.env.company
    )

    @api.depends('company_id')
    def _compute_funcionarios(self):
        today = date.today()
        now = datetime.now()
        company_id = self.env.company.id

        all_employees = self.env['hr.employee'].sudo().search([('company_id', '=', company_id)])

        employees_with_attendance = self.env['hr.attendance'].sudo().search([
            ('check_in', '>=', today.strftime('%Y-%m-%d 00:00:00')),
            ('check_in', '<=', now.strftime('%Y-%m-%d %H:%M:%S')),
            ('employee_id.company_id', '=', company_id)
        ]).mapped('employee_id')

        employees_without_attendance = all_employees.filtered(lambda e: e not in employees_with_attendance)

        absent_model = self.env['hr.absent.record'].sudo()

        for employee in employees_without_attendance:
            if not absent_model.search([('employee_id', '=', employee.id), ('absent_date', '=', today)]):
                absent_model.create({
                    'employee_id': employee.id,
                    'company_id': company_id,
                    'absent_date': today,
                })

        absent_model.search([
            ('employee_id', 'in', employees_with_attendance.ids),
            ('absent_date', '=', today)
        ]).unlink()

        for record in self:
            record.employee_ids = employees_without_attendance


class HrAbsentRecord(models.Model):
    _name = 'hr.absent.record'
    _description = 'Registro de Funcionários Ausentes'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Funcionário",
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company
    )
    absent_date = fields.Date(
        string="Data da Ausência",
        required=True,
        default=fields.Date.context_today
    )


class HrEmployeesWithoutCheckin(models.Model):
    _name = 'hr.employees.without.checkin'
    _description = 'Funcionários sem Check-in (Dinâmico)'
    _auto = False

    employee_id = fields.Many2one(
        'hr.employee',
        string="Funcionário",
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        readonly=True,
        copy=False,
        help="Empresa",
        default=lambda self: self.env.company
    )
    date = fields.Date(
        string="Data",
        compute='_compute_date',
        store=False
    )

    employee_name = fields.Char(
        string="Nome do Funcionário",
        related='employee_id.name',
        readonly=True,
        store=False
    )

    start_date = fields.Date(
        string="Data Inicial",
        readonly=True
    )
    end_date = fields.Date(
        string="Data Final",
        readonly=True
    )

    @api.depends_context('start_date', 'end_date')
    def _compute_date(self):

        start_date = self._context.get('start_date', fields.Date.today())
        end_date = self._context.get('end_date', fields.Date.today())
        for record in self:
            record.date = start_date

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):

        start_date = False
        end_date = False
        for arg in args:
            if isinstance(arg, (list, tuple)) and len(arg) == 3:
                if arg[0] == 'date' and arg[1] == '>=':
                    start_date = arg[2]
                elif arg[0] == 'date' and arg[1] == '<=':
                    end_date = arg[2]

        if not start_date or not end_date:
            start_date = fields.Date.today()
            end_date = fields.Date.today()

        domain = [
            ('employee_id', 'not in', self._get_employees_with_checkin(start_date, end_date)),
            ('company_id', '=', self.env.company.id)
        ]

        self = self.with_context(start_date=start_date, end_date=end_date)

        return super().search(domain, offset=offset, limit=limit, order=order, count=count)

    def _get_employees_with_checkin(self, start_date, end_date):
        """
        Retorna uma lista de IDs de funcionários que fizeram check-in no período.
        """
        self._cr.execute("""
            SELECT DISTINCT employee_id
            FROM hr_attendance
            WHERE check_in::date BETWEEN %s AND %s
        """, (start_date, end_date))
        return [row[0] for row in self._cr.fetchall()]

    def init(self):
        """
        Método init para recriar a view no banco de dados.
        """
        self._cr.execute("DROP VIEW IF EXISTS hr_employees_without_checkin CASCADE")
        self._cr.execute("""
            CREATE OR REPLACE VIEW hr_employees_without_checkin AS (
                SELECT
                    e.id AS id,
                    e.id AS employee_id,
                    e.company_id AS company_id
                FROM hr_employee e
                WHERE
                    e.company_id = %(company_id)s
                GROUP BY e.id, e.company_id
            )
        """, {
            'company_id': self.env.company.id
        })

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HrEmployeesWithoutCheckin, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type == 'tree':

            start_date = self._context.get('start_date', fields.Date.today())
            end_date = self._context.get('end_date', fields.Date.today())
            if isinstance(res, dict) and 'context' in res:
                res['context'].update({
                    'start_date': start_date,
                    'end_date': end_date
                })

        return res