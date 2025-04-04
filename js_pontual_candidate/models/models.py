from datetime import timedelta, time, date

from odoo.addons.resource.models.resource import float_to_time

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrAnnouncementTable(models.Model):
    _inherit = "hr.announcement"

    banner = fields.Binary("Banner", attachment=True)



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def get_available_periods(self):
        self.ensure_one()
        if not self.resource_calendar_id:
            return []

        periods = self.env['resource.calendar.attendance'].search([
            ('calendar_id', '=', self.resource_calendar_id.id)
        ]).mapped('day_period')

        return list(set(periods))


class ShiftSwap(models.Model):
    _name = 'shift.swap'
    _description = 'Troca de Turno'

    name = fields.Char('Referência', readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', 'Funcionário Solicitante', required=True)
    requested_employee_id = fields.Many2one('hr.employee', 'Funcionário Solicitado', required=True)
    current_shift_id = fields.Many2one('resource.calendar', 'Turno Atual', related='employee_id.resource_calendar_id')
    requested_shift_id = fields.Many2one('resource.calendar', 'Turno Solicitado',
                                         related='requested_employee_id.resource_calendar_id')

    date_from = fields.Date('Data Inicial', required=True)
    date_to = fields.Date('Data Final', required=True)

    swap_days_ids = fields.One2many('shift.day', 'swap_id', string='Dias de Troca')

    available_periods = fields.Many2many(
        'resource.calendar.attendance',
        compute='_compute_available_periods',
        string='Períodos Disponíveis'
    )

    day_period = fields.Selection(
        selection=lambda self: self._get_period_selection(),
        string='Período do Dia',
        required=True,
        default='all_day'
    )

    current_period_time = fields.Char('Horário Atual', compute='_compute_period_times')
    requested_period_time = fields.Char('Horário Solicitado', compute='_compute_period_times')

    reason = fields.Text('Motivo')
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('requested', 'Solicitado'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('canceled', 'Cancelado'),
    ], string='Status', default='draft', tracking=True)

    @api.depends('employee_id', 'requested_employee_id')
    def _compute_available_periods(self):
        for record in self:
            periods = self.env['resource.calendar.attendance']
            if record.employee_id.resource_calendar_id:
                periods |= record.employee_id.resource_calendar_id.attendance_ids
            if record.requested_employee_id.resource_calendar_id:
                periods |= record.requested_employee_id.resource_calendar_id.attendance_ids
            record.available_periods = periods

    def _get_period_selection(self):
        periods = self.env['resource.calendar.attendance'].search([])
        unique_periods = set(periods.mapped('day_period'))
        selection = [('all_day', 'Dia Todo')] + [(p, p.capitalize()) for p in unique_periods if p]
        return selection

    def _get_period_time(self, employee, period):
        if not employee or not employee.resource_calendar_id:
            return "N/A"

        attendances = self.env['resource.calendar.attendance'].search([
            ('calendar_id', '=', employee.resource_calendar_id.id)
        ], order='hour_from asc')

        if not attendances:
            return "Horário não definido"

        if period == 'all_day':
            hour_from = float_to_time(attendances[0].hour_from)
            hour_to = float_to_time(attendances[-1].hour_to)
            return f"{hour_from.strftime('%H:%M')} - {hour_to.strftime('%H:%M')}"
        else:
            attendance = attendances.filtered(lambda a: a.day_period == period)
            if not attendance:
                return "Horário não definido"

            hour_from = float_to_time(attendance[0].hour_from)
            hour_to = float_to_time(attendance[0].hour_to)
            return f"{hour_from.strftime('%H:%M')} - {hour_to.strftime('%H:%M')}"

    def _check_date_range(self):
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError(_('A data final deve ser posterior à data inicial.'))

    @api.onchange('date_from', 'date_to', 'employee_id', 'requested_employee_id', 'day_period')
    def _onchange_dates(self):
        """Atualiza os dias de troca quando algum dos campos relacionados muda"""
        for record in self:
            # Preserva todos os valores atuais antes de fazer qualquer alteração
            current_values = {
                'state': record.state,
                'reason': record.reason,
                # Adicione aqui outros campos que não devem ser resetados
            }

            # Gera os novos dias de troca
            record._generate_swap_days()

            # Restaura os valores que não devem ser alterados
            record.update(current_values)

    def _generate_swap_days(self):
        """Gera ou atualiza os dias de troca baseado nas datas e período selecionado"""
        self.ensure_one()

        if not all([self.date_from, self.date_to, self.employee_id, self.requested_employee_id, self.day_period]):
            return

        try:
            date_from = fields.Date.to_date(self.date_from)
            date_to = fields.Date.to_date(self.date_to)

            # Mantém os dias existentes que ainda estão no intervalo
            existing_days = {day.date: day for day in self.swap_days_ids}
            days_to_keep = []
            current_date = date_from

            while current_date <= date_to:
                current_date = fields.Date.to_date(current_date)
                date_str = fields.Date.to_string(current_date)

                if date_str in existing_days:
                    # Atualiza o dia existente
                    existing_days[date_str].write({
                        'is_working_day': self._check_working_day(current_date),
                    })
                    days_to_keep.append(existing_days[date_str].id)
                else:
                    # Cria novo dia
                    new_day = self.env['shift.day'].create({
                        'date': current_date,
                        'day_of_week': current_date.strftime('%A'),
                        'swap_id': self.id,
                        'is_working_day': self._check_working_day(current_date),
                    })
                    days_to_keep.append(new_day.id)

                current_date += timedelta(days=1)

            # Remove dias que não estão mais no intervalo
            self.swap_days_ids.filtered(lambda d: d.id not in days_to_keep).unlink()

        except Exception as e:
            raise UserError(_("Erro ao gerar dias de troca: %s") % str(e))

    def _check_working_day(self, date):
        self.ensure_one()
        date_dt = fields.Date.from_string(date)
        weekday = date_dt.weekday()

        if self.day_period == 'all_day':
            emp_working = self.employee_id.resource_calendar_id and \
                          self.env['resource.calendar.attendance'].search_count([
                              ('calendar_id', '=', self.employee_id.resource_calendar_id.id),
                              ('dayofweek', '=', str(weekday))
                          ]) > 0

            req_emp_working = self.requested_employee_id.resource_calendar_id and \
                              self.env['resource.calendar.attendance'].search_count([
                                  ('calendar_id', '=', self.requested_employee_id.resource_calendar_id.id),
                                  ('dayofweek', '=', str(weekday))
                              ]) > 0
        else:
            emp_working = self.employee_id.resource_calendar_id and \
                          self.env['resource.calendar.attendance'].search_count([
                              ('calendar_id', '=', self.employee_id.resource_calendar_id.id),
                              ('dayofweek', '=', str(weekday)),
                              ('day_period', '=', self.day_period)
                          ]) > 0

            req_emp_working = self.requested_employee_id.resource_calendar_id and \
                              self.env['resource.calendar.attendance'].search_count([
                                  ('calendar_id', '=', self.requested_employee_id.resource_calendar_id.id),
                                  ('dayofweek', '=', str(weekday)),
                                  ('day_period', '=', self.day_period)
                              ]) > 0

        return emp_working and req_emp_working

    @api.depends('day_period', 'employee_id', 'requested_employee_id')
    def _compute_period_times(self):
        for record in self:
            current_time = self._get_period_time(record.employee_id, record.day_period)
            record.current_period_time = current_time

            requested_time = self._get_period_time(record.requested_employee_id, record.day_period)
            record.requested_period_time = requested_time

    def _get_period_time(self, employee, period):
        if not employee or not employee.resource_calendar_id:
            return "N/A"

        attendances = self.env['resource.calendar.attendance'].search([
            ('calendar_id', '=', employee.resource_calendar_id.id)
        ], order='hour_from asc')

        if not attendances:
            return "Horário não definido"

        if period == 'all_day':
            min_hour_from = min(attendances.mapped('hour_from'))
            max_hour_to = max(attendances.mapped('hour_to'))

            hour_from = float_to_time(min_hour_from)
            hour_to = float_to_time(max_hour_to)
            return f"{hour_from.strftime('%H:%M')} - {hour_to.strftime('%H:%M')}"
        else:
            period_attendances = attendances.filtered(lambda a: a.day_period == period)

            if not period_attendances:
                return "Horário não definido"

            attendance = period_attendances[0]
            hour_from = float_to_time(attendance.hour_from)
            hour_to = float_to_time(attendance.hour_to)
            return f"{hour_from.strftime('%H:%M')} - {hour_to.strftime('%H:%M')}"

    def float_to_time(float_hour):
        if float_hour is False:
            return time(0, 0)
        return time(
            int(float_hour),
            int(round((float_hour % 1) * 60)))

    def action_request(self):
        invalid_days = self.swap_days_ids.filtered(lambda d: not d.is_working_day)
        if invalid_days:
            raise ValidationError(_(
                "Não é possível solicitar troca para os seguintes dias pois não são dias de trabalho para ambos funcionários:\n%s"
            ) % "\n".join(invalid_days.mapped('date')))

        self.write({'state': 'requested'})

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('shift.swap') or 'New'

        swap = super(ShiftSwap, self).create(vals)

        swap._generate_swap_days()

        return swap

    def action_request(self):
        self.write({'state': 'requested'})

    def action_approve(self):
        self.employee_id.resource_calendar_id = self.requested_shift_id.id
        self.requested_employee_id.resource_calendar_id = self.current_shift_id.id
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_cancel(self):
        self.write({'state': 'canceled'})

    def action_reset(self):
        self.write({'state': 'draft'})

class ShiftSwapDay(models.Model):
    _name = 'shift.day'
    _description = 'Dia de Troca de Turno'

    _order = 'date asc'

    swap_id = fields.Many2one('shift.swap', string='Troca', ondelete='cascade')
    date = fields.Date('Data', required=True)
    day_of_week = fields.Char('Dia da Semana', readonly=True)
    is_working_day = fields.Boolean('Dia de Trabalho', readonly=True)
    notes = fields.Text('Observações')


class CertificateRequest(models.Model):
    _name = 'certificate.request'
    _description = 'Solicitação de Certificados e Declarações'

    name = fields.Char(string="Número", readonly=True, default="Nova")
    employee_id = fields.Many2one('hr.employee', string="Funcionário", required=True)
    department_id = fields.Many2one('hr.department', string="Departamento", related='employee_id.department_id')
    request_date = fields.Date(string="Data da Solicitação", default=fields.Date.today, readonly=True)

    certificatetype = fields.Char(string="Tipo de Documento", required=True)

    supported_attachment_ids_count = fields.Integer(compute='_compute_supported_attachment_ids')

    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('requested', 'Solicitado'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('done', 'Concluído')],
        string="Status", default='draft', tracking=True)

    notes = fields.Text(string="Observações")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string="Anexos",
                                     domain=[('res_model', '=', 'certificate.request')])
    supported_attachment_ids = fields.Many2many(
        'ir.attachment', string="Attach File", compute='_compute_supported_attachment_ids',
        inverse='_inverse_supported_attachment_ids')

    @api.depends('attachment_ids')
    def _compute_supported_attachment_ids(self):
        for holiday in self:
            holiday.supported_attachment_ids = holiday.attachment_ids
            holiday.supported_attachment_ids_count = len(holiday.attachment_ids.ids)

    def _inverse_supported_attachment_ids(self):
        for holiday in self:
            holiday.attachment_ids = holiday.supported_attachment_ids

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nova') == 'Nova':
            vals['name'] = self.env['ir.sequence'].next_by_code('certificate.request') or 'Nova'
        return super(CertificateRequest, self).create(vals)

    def action_request(self):
        self.write({'state': 'requested'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_reset(self):
        self.write({'state': 'draft'})
