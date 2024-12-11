# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    folha_id = fields.Many2one('folhapagamento.folhapagamento', string='Folha de Pagamento')


class Folha(models.Model):
    _name = 'folha.folha'
    _description = 'folha.folha'

    name = fields.Char(string='Descrição')
    month = fields.Selection(
        [('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'), ('05', 'May'),
         ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'), ('10', 'October'),
         ('11', 'November'), ('12', 'December')],
        string='Month',
        required=True,
        help='Month related to the payroll'
    )

    departamento_id = fields.Many2one('hr.department', string='Departamento de RH')

    payslip_ids = fields.One2many(
        comodel_name='hr.payslip',
        inverse_name='folha_id',
        string='Payslips',
    )

    @api.depends('month')
    def _compute_payslips(self):
        """
        Este método é chamado automaticamente para recalcular o campo 'payslip_ids'
        sempre que o mês for alterado.
        """
        for record in self:
            if record.month:
                year = fields.Date.today().year  # Ano atual
                month = record.month
                start_date = f'{year}-{month}-01'
                # Usando o último dia do mês (28-31, dependendo do mês)
                end_date = f'{year}-{month}-28'  # Ajustar conforme o número de dias no mês
                # Atualiza os payslips associados ao mês
                payslips = self.env['hr.payslip'].search([
                    ('date_from', '>=', start_date),
                    ('date_to', '<=', end_date),
                ])
                record.payslip_ids = payslips
            else:
                record.payslip_ids = False

