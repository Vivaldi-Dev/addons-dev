from odoo import models, fields, api


class LastRecord(models.Model):
    _name = 'last.record'
    _description = 'Modelo para armazenar últimos registros de hr.leave e hr.loan'

    employee_id = fields.Many2one('hr.employee', string='Funcionário', required=True, ondelete='cascade')

    leave_name = fields.Char(string='Nome do Último Registro de Férias')
    leave_state = fields.Selection(related='last_leave_id.state', string='Estado do Último Registro de Férias',
                                   store=True)
    leave_date = fields.Date(string='Data do Último Registro de Férias')
    last_leave_id = fields.Many2one('hr.leave', string='Último Registro de Férias')

    loan_name = fields.Char(string='Nome do Último Registro de Empréstimo')
    loan_state = fields.Selection(related='last_loan_id.state', string='Estado do Último Registro de Empréstimo',
                                  store=True)
    loan_date = fields.Date(string='Data do Último Registro de Empréstimo')
    last_loan_id = fields.Many2one('hr.loan', string='Último Registro de Empréstimo')

    swap_name = fields.Char(string='Última Troca de Turno')
    swap_state = fields.Selection(related='last_swap_id.state', store=True)
    last_swap_id = fields.Many2one('shift.swap', string='Registro de Troca')
    swap_date = fields.Datetime(string='Data da Troca')

    certificate_name = fields.Char(string='Último Certificado')
    certificate_state = fields.Selection(related='last_certificate_id.state', store=True)
    last_certificate_id = fields.Many2one('certificate.request', string='Registro de Certificado')
    certificate_date = fields.Datetime(string='Data do Certificado')

    create_date = fields.Datetime(string='Data de Criação', default=fields.Datetime.now)

    @api.model
    def create_last_record(self, employee_id):
        last_record = self.search([('employee_id', '=', employee_id)], limit=1)

        last_leave = self.env['hr.leave'].search(
            [('employee_id', '=', employee_id)],
            order='request_date_from desc',
            limit=1
        )

        last_loan = self.env['hr.loan'].search(
            [('employee_id', '=', employee_id)],
            order='date desc',
            limit=1
        )

        last_swap = self.env['shift.swap'].search(
            [('employee_id', '=', employee_id)],
            order='create_date desc', limit=1
        )

        last_certificate = self.env['certificate.request'].search(
            [('employee_id', '=', employee_id)],
            order='create_date desc', limit=1
        )

        vals = {
            'employee_id': employee_id,
            'leave_name': last_leave.name if last_leave else False,
            'leave_date': last_leave.request_date_from if last_leave else False,
            'last_leave_id': last_leave.id if last_leave else False,
            'loan_name': last_loan.name if last_loan else False,
            'loan_date': last_loan.date if last_loan else False,
            'last_loan_id': last_loan.id if last_loan else False,
            'last_swap_id': last_swap.id if last_swap else False,
            'swap_date': last_swap.create_date if last_swap else False,

            'certificate_name': last_certificate.certificatetype if last_certificate else False,
            'last_certificate_id': last_certificate.id if last_certificate else False,
            'certificate_date': last_certificate.request_date if last_certificate else False,

        }

        if last_record:
            last_record.write(vals)
        else:
            last_record = self.create(vals)

        return last_record


class HrLeaveInherited(models.Model):
    _inherit = "hr.leave"

    @api.model_create_multi
    def create(self, vals_list):
        holidays = super(HrLeaveInherited, self).create(vals_list)

        for holiday in holidays:
            self.env['last.record'].create_last_record(holiday.employee_id.id)

        return holidays

class HrLoanInherited(models.Model):
    _inherit = 'hr.loan'

    @api.model
    def create(self, values):
        loan = super(HrLoanInherited, self).create(values)

        self.env['last.record'].create_last_record(values['employee_id'])

        return loan

class ShiftSwap(models.Model):
    _inherit = 'shift.swap'

    @api.model
    def create(self, vals_list):
        swaps = super(ShiftSwap, self).create(vals_list)
        for swap in swaps:
            self.env['last.record'].create_last_record(swap.employee_id.id)
        return swaps

    def write(self, vals):
        res = super(ShiftSwap, self).write(vals)
        if 'state' in vals:
            for swap in self:
                self.env['last.record'].create_last_record(swap.employee_id.id)
        return res

class CertificateRequest(models.Model):
    _inherit = 'certificate.request'

    @api.model_create_multi
    def create(self, vals_list):
        certificates = super(CertificateRequest, self).create(vals_list)
        for certificate in certificates:
            if 'employee_id' in certificate:
                self.env['last.record'].create_last_record(certificate.employee_id.id)
        return certificates

    def write(self, vals):
        res = super(CertificateRequest, self).write(vals)
        if 'state' in vals:
            for certificate in self:
                self.env['last.record'].create_last_record(certificate.employee_id.id)
        return res