# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from datetime import date, datetime, time
from datetime import timedelta
import babel

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.onchange('struct_id')
    def _onchange_struct_id(self):
        res = []
        self.input_line_ids = [(5, 0, 0)]
        if self.struct_id:
            rule_ids = self.env['hr.payroll.structure'].browse(self.struct_id.id).get_all_rules()
            sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
            inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')

            for input in inputs:
                input_data = {
                    'name': input.name,
                    'code': input.code,
                    'contract_id': self.contract_id.id,
                }

                res.append((0, 0, input_data))

        self.input_line_ids = res


