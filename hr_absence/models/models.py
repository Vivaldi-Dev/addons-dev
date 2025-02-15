# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class HrAbsence(models.Model):
    _name = 'hr.absence'
    _description = 'Employee Absence Management'

    description = fields.Text('Description')
    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)

    departamento_id = fields.Many2one('hr.department', string='Departamento')
    company_id = fields.Many2one('res.company', string='Company', readonly=False, copy=False, help="Company",
                                 default=lambda self: self.env['res.company']._company_default_get())

    absence_info_ids = fields.One2many(
        'hr.info', 'hr_absence_id', string='Funcionários Ausentes')

    @api.onchange('date_start', 'date_end', 'departamento_id', 'company_id')
    def search_absentees(self):
        if not self.date_start or not self.date_end:
            return

        employees = self.env['hr.employee'].search([
            ('company_id', '=', self.company_id.id)
        ])

        attendance_records = self.env['hr.attendance'].search([
            ('employee_id', 'in', employees.ids),
            ('check_in', '>=', self.date_start),
            ('check_in', '<=', self.date_end)
        ])

        present_employee_ids = attendance_records.mapped('employee_id.id')

        absent_employees = employees.filtered(lambda e: e.id not in present_employee_ids)

        self.absence_info_ids = [(5, 0, 0)]

        for employee in absent_employees:
            self.absence_info_ids = [(0, 0, {
                'employee_id': employee.id,
                'job_position': employee.job_id.name,
            })]

class HrAbsenceInfo(models.Model):
    _name = 'hr.info'
    _description = 'Employee Absence Information'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    job_position = fields.Char(string='Job Position')
    hr_absence_id = fields.Many2one('hr.absence', string='Folha de Pagamento', ondelete='cascade')
