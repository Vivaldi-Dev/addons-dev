# -*- coding: utf-8 -*-


from odoo import models, fields, api
from datetime import datetime
from datetime import date


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related="employee_id.company_id",
        store=True,
        readonly=True,
        default=lambda self: self.env.company.id,

    )

    @api.model
    def _search_no_check_in(self, operator, value):
        today = date.today()
        today_start = today.strftime('%Y-%m-%d 00:00:00')
        today_end = today.strftime('%Y-%m-%d 23:59:59')

        attendance_records = self.env['hr.attendance'].search([
            ('check_in', '>=', today_start),
            ('check_in', '<=', today_end),
            ('company_id', '=', self.env.company.id),  # Filtra pela empresa atual
        ])
        employee_ids_with_check_in = attendance_records.mapped('employee_id.id')

        return [('id', 'not in', employee_ids_with_check_in)]

    has_checked_in_today = fields.Boolean(
        string="Checked In Today",
        compute="_compute_has_checked_in_today",
        store=False,
        search=_search_no_check_in,
    )
