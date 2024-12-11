  # -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api
from odoo.exceptions import UserError

class AvaliarTemplate(models.Model):
    _name = "avaliar.template"
    _description = 'Avaliar Template'


    name = fields.Char("Name", required=True)
    avaliar_ids = fields.Many2many("avaliacaodesempenho.avaliacaodesempenho", 'avaliar_ids_rel', string="Avaliar")

class comissaoTemplate(models.Model):
    _name = "comissao.template"
    _description = 'Comissao Template'


    name = fields.Char("Name", required=True)
    comissao_id = fields.Many2many("comissao.avaliadora", string="Comissao")

class ComissaoType(models.Model):
    _name = 'comissao.tipo'
    _description = 'Tipo de Comissao'

    name = fields.Char(string='Name', required=True)
    departamento = fields.Many2one('hr.department', string='Departamento', required=True)
    cargo = fields.Char(string='Cargo', required=True)
    funcionario_id = fields.Many2one('hr.employee', string='Funcionario', ondelete='cascade', required=True)
    funcionario_avaliacao_id = fields.Many2one('avaliar.funcionario', string='Funcionario Avaliacao', ondelete='cascade')


class Avalia(models.Model):
    _name = "avaliar.funcionario"
    _description = "Avaliar Funcionario"


    name = fields.Many2one('hr.employee', string='Nome', ondelete='cascade', required=True)
    cargo = fields.Many2one(related='name.job_id', string='Cargo', store=True)
    departamento = fields.Many2one('hr.department', string='Departamento', store=True)
    avaliador = fields.Many2one('hr.employee', string='Avaliador', ondelete='cascade', required=True, default=lambda self: self.env.user.employee_id.id)
    # avaliador = fields.Many2one('hr.employee', string='Avaliador', ondelete='cascade', required=True)
    cargo_avaliador = fields.Many2one(related='avaliador.job_id', string="Cargo", required=True)
    data_aprovacao = fields.Datetime(string="Data", required=True, default=fields.Datetime.now)
    anotacoes = fields.Text(string='Anotacoes', required=True)
    assinatura_colaborador = fields.Char(string="Ass. Colaborador")
    assinatura_avaliador = fields.Char(string="Ass. do Avaliador")
    assinatura_responsavel = fields.Char(string="Ass.do responsavel pelo RH")
    status = fields.Selection(
        [('novo', 'Novo'),
         ('espera', 'Em espera'),
         ('aprovar', 'Aprovado'),
         ('concluir', 'Concluido'),
         ('cancelar', 'Cancelado'),
         ('rejeitar', 'Rejeitado')],

        default="novo",
        string="Status", tracking=True)
    check_list = fields.Many2many('avaliar.template', 'avaliar_teste_rel', string="Tipo de competência", required =True)
    custom_checklist_ids = fields.One2many("avaliacao.tipo", 'funcionario_id', string="Competência", required=True)
    relatorio_id = fields.Many2one('relatorio.avaliacoes', string="Relatório")
    total_nota = fields.Float(string='Total Nota', compute='calcular_nota_total', store=True)
    comissao_list = fields.Many2one('comissao.template', string="Comissao Avaliadora")
    comissao_checklist_ids = fields.One2many("comissao.tipo", 'funcionario_avaliacao_id', string="Comissao",required=True)
    should_hide_total_nota = fields.Boolean(string='Should Hide Total Nota', compute='_compute_should_hide_total_nota')

    @api.onchange('comissao_list')
    def _onchange_avaliador(self):
        if self.avaliador:
            domain = [('comissao_id.avaliador_ids', 'in', [self.avaliador.id])]
            comissao_templates = self.env['comissao.template'].search(domain)
            if comissao_templates:
                return {'domain': {'comissao_list': [('id', 'in', comissao_templates.ids)]}}
            else:
                return {'domain': {'comissao_list': []}}
        else:
            return {'domain': {'comissao_list': []}}
    @api.onchange('check_list')
    def onchange_check_list(self):
        update_ids = []
        for checklist_template in self.check_list:
            for checklist_item in checklist_template.avaliar_ids:
                new_id = self.env["avaliacao.tipo"].create({
                    'name': checklist_item.name,
                    'description': checklist_item.description,
                    'peso': checklist_item.peso,
                    'escala': checklist_item.escala,
                    'competencia': checklist_item.competencia,
                    'funcionario_id': self.id,  # Link to current project
                })
                update_ids.append(new_id.id)
        self.custom_checklist_ids = [(6, 0, update_ids)]

    @api.depends('avaliador')
    def _compute_comissao(self):
        user = self.env.user
        domain = {'comissao_list': []}
        comissoes = self.env['comissao.template'].search([('comissao_id.avaliador_ids', 'in', [user.id])])
        domain = {'comissao_list': [('id', 'in', comissoes.ids)]}

        return {'domain': domain}

    @api.depends('custom_checklist_ids.nota')
    def _compute_should_hide_total_nota(self):
        for record in self:
            hide = any(not checklist.nota for checklist in record.custom_checklist_ids)
            record.should_hide_total_nota = hide

    @api.constrains('custom_checklist_ids')
    def _check_checklist_not_empty(self):
        for record in self:
            if any(not checklist.nota for checklist in record.custom_checklist_ids):
                raise UserError("Por favor, adicione as notas na avaliação antes de salvar.")

    @api.model
    def create(self, vals):
        # Verifica se todas as notas estão preenchidas antes de criar o registro
        if any(not checklist['nota'] for checklist in vals.get('custom_checklist_ids', []) if
               isinstance(checklist, dict)):
            raise UserError("Por favor, adicione todas as notas na avaliação antes de salvar.")
        res = super(Avalia, self).create(vals)
        return res

    def write(self, vals):
        # Verifica se todas as notas estão preenchidas antes de atualizar o registro
        if 'custom_checklist_ids' in vals:
            for checklist in vals.get('custom_checklist_ids', []):
                if isinstance(checklist, dict) and not checklist.get('nota'):
                    raise UserError("Por favor, adicione todas as notas na avaliação antes de salvar.")
        res = super(Avalia, self).write(vals)
        return res

    @api.depends('custom_checklist_ids.peso', 'custom_checklist_ids.nota', 'check_list')
    def calcular_nota_total(self):
        for record in self:
            total_nota_essenciais = 0
            total_nota_gerenciais = 0
            max_score_essenciais = 0
            max_score_gerenciais = 0

            # Cria dicionários para categorizar as notas
            checklist_dict = {check.name: [] for check in record.check_list}

            for item in record.custom_checklist_ids:
                checklist_dict[item.competencia].append(item)
            # Calcula as notas para "ESSENCIAIS"
            if 'ESSENCIAIS' in checklist_dict:
                for item in checklist_dict['ESSENCIAIS']:
                    total_nota_essenciais += item.nota
                    max_score_essenciais += item.peso

            # Calcula as notas para "GERENCIAIS"
            if 'GERENCIAIS' in checklist_dict:
                for item in checklist_dict['GERENCIAIS']:
                    total_nota_gerenciais += item.nota * 2
                    max_score_gerenciais += item.peso * 2

            # Calculate total score
            total_nota = total_nota_essenciais + total_nota_gerenciais
            max_score = max_score_essenciais + max_score_gerenciais

            if max_score > 0:
                record.total_nota = (total_nota / max_score) * 100
            else:
                record.total_nota = 0

    # Metodo que traz as comissoes com base no nome
    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.departamento = self.name.department_id.id  # Ajustando para pegar o ID do departamento
            domain = [('comissao_id.funcionario_ids', 'in', [self.name.id])]
            comissao_templates = self.env['comissao.template'].search(domain)
            if comissao_templates:
                return {'domain': {'comissao_list': [('id', 'in', comissao_templates.ids)]}}
            else:
                return {'domain': {'comissao_list': []}}
        else:
            return {'domain': {'comissao_list': []}}
    @api.onchange('comissao_list')
    def _onchange_comissao_list(self):
        if self.comissao_list:
            comissao_template = self.comissao_list.comissao_id

            self.check_list = comissao_template.competencia_list

            funcionarios = comissao_template.funcionario_ids
            avaliadores = comissao_template.avaliador_ids

            funcionario_options = [(funcionario.id, funcionario.name) for funcionario in funcionarios]
            avaliador_options = [(avaliador.id, avaliador.name) for avaliador in avaliadores]

            funcionario_options.insert(0, (False, ''))
            avaliador_options.insert(0, (False, ''))

            return {
                'domain': {
                    'avaliador': [('id', 'in', avaliadores.ids)],
                    'name': [('id', 'in', funcionarios.ids)]
                }
            }
        else:
            return {
                'domain': {
                    'avaliador': [],
                    'name': []
                }
            }

    @api.onchange('cargo_avaliador')
    def _onchange_cargo_avaliador(self):
        if self.cargo_avaliador:
            return {'domain': {'avaliador': [('job_id.id', '=', self.cargo_avaliador.id)]}}
        else:
            return {'domain': {'avaliador': []}}
    @api.onchange('cargo')
    def _onchange_cargo(self):
        if self.cargo:
            return {'domain': {'name': [('job_id.id', '=', self.cargo.id)]}}
        else:
            return {'domain': {'name': []}}

    @api.onchange('comissao_list')
    def _onchange_ccomissao_list(self):
        if self.comissao_list:
            update_ids = []
            for comissao_template in self.comissao_list:
                for checklist_item in comissao_template.comissao_id:
                    departamento_id = False
                    if checklist_item.funcionario_ids:
                        funcionario = checklist_item.funcionario_ids.filtered(lambda f: f.department_id)[:1]
                        if funcionario:
                            departamento_id = funcionario.department_id.id
                    new_id = self.env["comissao.tipo"].create({
                        'name': checklist_item.name,
                        'cargo': checklist_item.cargo,
                        'departamento': departamento_id,
                        'funcionario_id': funcionario.id,  # Corrigido para usar funcionario.id
                        'funcionario_avaliacao_id': self.id,
                    })
                    update_ids.append(new_id.id)

            self.comissao_checklist_ids = [(6, 0, update_ids)]

    @api.model
    def create_comissao_for_employee(self):
        employees_without_comissao = self.env['hr.employee'].search(
            [('id', 'not in', self.env['avaliar.funcionario'].mapped('name.id'))])
        for employee in employees_without_comissao:
            comissao_template_id = self.env['comissao.template'].search([], limit=1)  # Assuming you have a comissao.template to assign
            if comissao_template_id:
                self.env['avaliar.funcionario'].create({
                    'name': employee.id,
                    'cargo': employee.job_id.name,
                    'departamento': employee.department_id.id,
                    'comissao_list': [(4, comissao_template_id.id)],
                })

    def action_send(self):
        for rec in self:
            rec.write({
                'status': 'espera',
                'assinatura_colaborador': self.name.name,
            })

        return True
    def action_cancelar(self):
        self.write({'status': 'cancelar'})

    def action_aprove(self):
        for record in self:
            record.refresh()
            if not record.exists():
                raise UserError("O registro não existe ou foi excluído.")

            if record.status != 'espera':
                raise UserError("A transição de estado é permitida apenas de 'Em espera' para 'Aprovado'.")
            # Atualizar o estado e chamar o método update_relatorio
            record.write({'status': 'aprovar',
                          'assinatura_avaliador': self.avaliador.name
                          })
    def action_concluir(self):
        self.write({'status': 'concluir'})

    def action_rejeitar(self):

        self.write({'status': 'rejeitar'})



