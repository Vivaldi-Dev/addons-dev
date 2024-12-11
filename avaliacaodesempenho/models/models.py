
from odoo import models, fields, api,  exceptions
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class AvaliacaoDashboard(models.Model):
    _name = 'avaliacao.dashboard'
    _description = 'Dashboard de Avaliações'

    total_novas = fields.Integer(string='Total de Novas Avaliações')
    total_a_serem_avaliadas = fields.Integer(string='Total de Avaliações a Serem Avaliadas')
    total_canceladas = fields.Integer(string='Total de Avaliações Canceladas')


class avaliacaodesempenho(models.Model):
    _name = 'avaliacaodesempenho.avaliacaodesempenho'
    _description = 'avaliacaodesempenho.avaliacaodesempenho'

    name = fields.Char(string='Name', required=True)
    description = fields.Html(string='Descricao', required=True)
    peso = fields.Float(string='Peso')
    escala = fields.Char(string='Escala', required=True)
    competencia = fields.Char(string="Competencia", required=True)


class ComissaAvaliadora(models.Model):
    _name = 'comissao.avaliadora'
    _description = 'Comissao Valiadora'

    name = fields.Char(string='Nome', required=True)
    funcionario_ids = fields.Many2many('hr.employee', string='Funcionários',relation='comissao_avaliadora_funcionario_rel', required=True)
    cargo = fields.Many2one(related='funcionario_ids.job_id', string='Cargo', store=True)
    departamento_ids = fields.Many2many('hr.department', string='Departamentos', required=True)
    avaliador_ids = fields.Many2many('hr.employee', string='Avaliadores', relation='comissao_avaliadora_avaliador_rel', required=True)
    competencia_list = fields.Many2many('avaliar.template', 'avaliar_comissao_rel', string="Tipo de competência", required =True)

    @api.onchange('departamento_ids')
    def _onchange_departamento_ids(self):
        if self.departamento_ids:
            domain = [('department_id', 'in', self.departamento_ids.ids)]
            return {'domain': {'funcionario_ids': domain}}
        return {'domain': {'funcionario_ids': []}}

    @api.depends('funcionario_ids')
    def _compute_cargos(self):
        for record in self:
            record.cargo_ids = [(6, 0, record.funcionario_ids.mapped('job_id').ids)]

    def remove_funcionario(self, employee_id):
        self.ensure_one()
        if employee_id in self.funcionario_ids.ids:
            self.write({
                'funcionario_ids': [(3, employee_id)]
            })

    @api.onchange('departamento_ids')
    def _onchange_departamento_ids(self):
        domain = [('department_id', 'in', self.departamento_ids.ids)]
        funcionarios = self.env['hr.employee'].search(domain)
        self.funcionario_ids = [(6, 0, funcionarios.ids)]


    @api.onchange('departamento_ids')
    def _onchange_departamento_ids(self):
        domain = [('department_id', 'in', self.departamento_ids.ids)]
        funcionarios = self.env['hr.employee'].search(domain)
        self.funcionario_ids = [(6, 0, funcionarios.ids)]
    def remove_funcionario(self, employee_id):
        self.ensure_one()

class AvaliacaoType(models.Model):
    _name = 'avaliacao.tipo'
    _description = 'Tipo de Avaliacao'

    name = fields.Char(string='Name', required=True)
    description = fields.Html(string='Descricao', required=True)
    peso = fields.Float(string='Peso')
    escala = fields.Char(string='Escala', required=True)
    nota = fields.Float(string="Nota Atribuida")
    competencia = fields.Char(string="Competencia")
    trimestre1 = fields.Char(string="1º Trimestre")
    trimestre2 = fields.Char(string="2º Trimestre")
    trimestre3 = fields.Char(string="3º Trimestre")
    trimestre4 = fields.Char(string="4º Trimestre")
    funcionario_id = fields.Many2one('avaliar.funcionario', string='Funcionario', ondelete='cascade')
    individual_id = fields.Many2one('avaliacao.individual', string='Funcionario', ondelete='cascade')

    @api.model
    def create(self, vals):
        if vals.get('trimestre2') or vals.get('trimestre3') or vals.get('trimestre4'):
            raise exceptions.ValidationError("Você não pode preencher Trimestres posteriores durante a criação.")
        return super(AvaliacaoType, self).create(vals)

    def write(self, vals):
        for record in self:
            if 'trimestre1' in vals:
                if record.trimestre2 or record.trimestre3 or record.trimestre4:
                    raise exceptions.ValidationError(
                        "Não é permitido editar Trimestre 1 após o preenchimento de trimestres subsequentes.")
            if 'trimestre2' in vals:
                if record.trimestre3 or record.trimestre4:
                    raise exceptions.ValidationError(
                        "Não é permitido editar Trimestre 2 após o preenchimento dos trimestres subsequentes.")
            if 'trimestre3' in vals:
                if record.trimestre4:
                    raise exceptions.ValidationError(
                        "Não é permitido editar Trimestre 3 após o preenchimento do Trimestre 4.")
        return super(AvaliacaoType, self).write(vals)

    @api.constrains('nota', 'escala')
    def _check_nota_escala(self):
        for avaliacao in self:
            if avaliacao.nota > float(avaliacao.escala):
                raise ValidationError("A nota não pode ser maior que a escala. Verifique e ajuste a nota.")

    @api.onchange('nota', 'escala')
    def _onchange_nota_escala(self):
        if self.nota > float(self.escala):
            return {
                'warning': {
                    'title': "Nota Inválida",
                    'message': "A nota não pode ser maior que a escala. Verifique e ajuste a nota."
                }
            }

    @api.depends('nota', 'escala')
    def _compute_color_nota(self):
        for record in self:
            if record.nota > float(record.escala):
                record.color_nota = 'red'
            else:
                record.color_nota = 'black'


# class FuncionarioAvaliacao(models.Model):
#     _inherit = 'hr.employee'
#     custom_checklist = fields.Float("Checklist Completed")
#     comissao = fields.Many2many('comissao.template', string="comissao ")
#     @api.onchange('check_list')
#     def onchange_check_list(self):
#         update_ids = []
#         for checklist_template in self.check_list:
#             for checklist_item in checklist_template.checklist_ids:
#                 new_id = self.env["avaliacao.tipo"].create({
#                     'name': checklist_item.name,
#                     'description': checklist_item.description,
#                     'peso': checklist_item.peso,
#                     'escala': checklist_item.escala,
#                     'funcionario_id': self.id,  # Link to current project
#                 })
#                 update_ids.append(new_id.id)
#         self.custom_checklist_ids = [(6, 0, update_ids)]

