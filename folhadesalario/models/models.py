from odoo import models, fields, api

class CompanyInfo(models.Model):
    _name = 'company.info'
    _description = 'Informações da Empresa'

    name = fields.Char("Nome da Empresa", required=True)
    logo = fields.Binary("Logo da Empresa")
    nuit = fields.Char("Nuit")
    department = fields.Char("Departamento")
    report_month_year = fields.Datetime("Referente ao Mês/Ano", required=True)

    hr_department = fields.Char("Departamento de RH", )

    approved_by = fields.Many2one('res.users', string="Aprovado Por")

    payroll_income_ids = fields.One2many('hr.payroll', 'company_info_id', string="Remuneração")
    payroll_discount_ids = fields.One2many('hr.payroll', 'company_info_id', string="Descontos")

class Payroll(models.Model):
    _name = 'hr.payroll'
    _description = 'Folha de Salários'

    employee_code = fields.Char("Código", required=True)
    employee_name = fields.Char("Nome", required=True)
    employee_position = fields.Char("Função", required=True)
    base_salary = fields.Float("Salário Base", required=True)
    incentive = fields.Float("Incentivo", default=0.0)
    overtime = fields.Float("Horas Extras", default=0.0)
    others_income = fields.Float("Diversos (Rendimento)", default=0.0)
    total_income = fields.Float("Total Remuneração", compute="_compute_total_income", store=True)

    inss = fields.Float("INSS", default=0.0)
    irps = fields.Float("IRPS", default=0.0)
    absences = fields.Float("Faltas", default=0.0)
    others_discount = fields.Float("Diversos (Desconto)", default=0.0)
    total_discount = fields.Float("Total Descontos", compute="_compute_total_discount", store=True)
    net_pay = fields.Float("Valor a Receber", compute="_compute_net_pay", store=True)

    company_info_id = fields.Many2one('company.info', string="Informações da Empresa")

    @api.depends('base_salary', 'incentive', 'overtime', 'others_income')
    def _compute_total_income(self):
        for record in self:
            record.total_income = (
                record.base_salary + record.incentive + record.overtime + record.others_income
            )

    @api.depends('inss', 'irps', 'absences', 'others_discount')
    def _compute_total_discount(self):
        for record in self:
            record.total_discount = (
                record.inss + record.irps + record.absences + record.others_discount
            )

    @api.depends('total_income', 'total_discount')
    def _compute_net_pay(self):
        for record in self:
            record.net_pay = record.total_income - record.total_discount
