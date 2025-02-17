# -*- coding: utf-8 -*-

from odoo import models, fields, api


class js_pontual(models.Model):
    _name = 'js_pontual.js_pontual'
    _description = 'js_pontual.js_pontual'

    @api.model
    def get_data_for_js_pontual(self, start_date, end_date, company_id):
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

        data = {
            'total_presents': len(presents),
            'present_list': presents,
            'total_absents': len(absents),
            'absent_list': absents
        }

        return data
