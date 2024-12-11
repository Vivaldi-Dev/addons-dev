  # -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
class Individual(models.Model):
    _name = "avaliacao.individual"
    _description = "Avaliacao Individual"


    name = fields.Many2one('hr.employee', string='Nome', ondelete='cascade', required=True)
    cargo = fields.Many2one('hr.job', string='Cargo', related='name.job_id', store=True)
    departamento = fields.Many2one('hr.department', related='name.department_id', string='Departamento', store=True)
    avaliador = fields.Many2one('hr.employee', string='Avaliador', ondelete='cascade', required=True)
    cargo_avaliador = fields.Many2one('hr.job', related='avaliador.job_id', string="Cargo do Avaliador", required=True)
    data_aprovacao = fields.Datetime(string="Data de Aprovação", required=True, default=fields.Datetime.now)
    anotacoes = fields.Char(string='Anotações', required=True)
    status = fields.Selection(
        [('novo', 'Novo'),
         ('avaliar', 'Avaliado'),
         ('cancelar', 'Cancelado')],
        default="novo",
        string="Status", tracking=True)
    check_individual = fields.Many2many('avaliar.template', 'avaliacao_individual_template_rel', 'individual_id', 'template_individual_id', string="Tipo de competência", required=True)
    custom_individual_ids = fields.One2many('avaliacao.tipo', 'individual_id', string="Competências", required=True)

    @api.onchange('check_individual')
    def onchange_check_list(self):
        update_ids = []
        for checklist_template in self.check_individual:
            for checklist_item in checklist_template.avaliar_ids:
                new_id = self.env["avaliacao.tipo"].create({
                    'name': checklist_item.name,
                    'description': checklist_item.description,
                    'escala': checklist_item.escala,
                    'individual_id': self.id,

                })
                update_ids.append(new_id.id)

        self.custom_individual_ids = [(6, 0, update_ids)]