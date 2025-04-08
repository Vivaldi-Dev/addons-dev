import time

from odoo import models, api, fields


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_inputs(self, contract_ids, date_to, date_from):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)

        contract_obj = self.env['hr.contract']
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        lon_obj = self.env['hr.loan'].search([('employee_id', '=', emp_id.id), ('state', '=', 'approve')])

        total_loan_amount = 0
        total_discount_amount = 0
        loan_line_ids = []
        discount_line_ids = []

        for loan in lon_obj:
            for loan_line in loan.loan_lines:
                if date_to <= loan_line.date <= date_from and not loan_line.paid:
                    if loan.is_desconto:
                        total_discount_amount += loan_line.amount
                        discount_line_ids.append(loan_line.id)
                    else:
                        total_loan_amount += loan_line.amount
                        loan_line_ids.append(loan_line.id)

        if total_loan_amount > 0:
            for result in res:
                if result.get('code') == 'DPE':
                    result['amount'] = total_loan_amount
                    result['loan_line_ids'] = [(6, 0, loan_line_ids)]

        if total_discount_amount > 0:
            for result in res:
                if result.get('code') == 'DD':
                    result['amount'] = total_discount_amount
                    result['loan_line_ids'] = [(6, 0, discount_line_ids)]

        return res

