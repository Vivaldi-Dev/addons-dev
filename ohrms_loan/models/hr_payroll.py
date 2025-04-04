# -*- coding: utf-8 -*-
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")

    loan_line_ids = fields.Many2many(
        'hr.loan.line', string="Loan Installments", help="Loan installments related to this payslip input"
    )

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # Nuevos campos
    bank_name = fields.Char(string="Banco", compute="_compute_bank_details", store=True)
    account_number = fields.Char(string="Número da Conta", compute="_compute_bank_details", store=True)
    net_salary = fields.Float(string="Salário Líquido", compute="_compute_net_salary", store=True)

    @api.depends('employee_id')
    def _compute_bank_details(self):
        for payslip in self:
            partner = payslip.employee_id.address_home_id
            if partner:
                payslip.bank_name = partner.bank_ids and partner.bank_ids[0].bank_id.name or ''
                payslip.account_number = partner.bank_ids and partner.bank_ids[0].acc_number or ''
            else:
                payslip.bank_name = ''
                payslip.account_number = ''

    @api.depends('line_ids')
    def _compute_net_salary(self):
        for payslip in self:
            net_line = payslip.line_ids.filtered(lambda line: line.code == 'NET')
            payslip.net_salary = net_line.total if net_line else 0.0

    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        contract_ids = []

        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(date_from), "%Y-%m-%d")))
        locale = self.env.context.get('lang') or 'en_US'
        self.name = _('Salary Slip of %s for %s') % (
            employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
        self.company_id = employee.company_id

        if not self.env.context.get('contract') or not self.contract_id:
            contract_ids = self.get_contract(employee, date_from, date_to)
            if not contract_ids:
                return
            self.contract_id = self.env['hr.contract'].browse(contract_ids[0])

        if not self.contract_id.struct_id:
            return
        self.struct_id = self.contract_id.struct_id

        # computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        worked_days_lines = self.worked_days_line_ids.browse([])
        for r in worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(r)
        self.worked_days_line_ids = worked_days_lines
        if contracts:
            print(date_from, date_to, '001qq')
            input_line_ids = self.get_inputs(contracts, date_from, date_to)
            input_lines = self.input_line_ids.browse([])
            for r in input_line_ids:
                input_lines += input_lines.new(r)
            self.input_line_ids = input_lines
        return

    def get_inputs(self, contract_ids, date_to, date_from):
        """This Compute the other inputs to employee payslip.
                           """
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)

        contract_obj = self.env['hr.contract']
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        lon_obj = self.env['hr.loan'].search([('employee_id', '=', emp_id.id), ('state', '=', 'approve')])

        total_loan_amount = 0  # Monto total de préstamos normales
        total_discount_amount = 0  # Monto total de préstamos con descuento
        loan_line_ids = []  # Referencias a líneas de crédito normales
        discount_line_ids = []  # Referencias a líneas de descuento

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

            # Si hay montos de descuentos, los agregamos al código 'DES_DIV'
        if total_discount_amount > 0:
            for result in res:
                if result.get('code') == 'DD':
                    result['amount'] = total_discount_amount
                    result['loan_line_ids'] = [(6, 0, discount_line_ids)]

        return res

    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_line_ids:
                for loan_line in line.loan_line_ids:
                    loan_line.paid = True
                    loan_line.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()
