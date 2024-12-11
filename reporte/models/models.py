from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountAccount(models.Model):
    _inherit = 'account.account'

    subconta_ids = fields.One2many('subconta.subconta', 'account_id', string="Subcontas")
    computed_balance = fields.Float(string="Saldo Calculado", compute='_compute_computed_balance', store=True)

    @api.depends('subconta_ids.balance', 'subconta_ids.operation_type')
    def _compute_computed_balance(self):
        """Calcula o saldo da conta mãe somando ou subtraindo os saldos das subcontas."""
        for account in self:
            total_balance = 0.0
            for subconta in account.subconta_ids:
                if subconta.operation_type == 'add':
                    total_balance += subconta.balance
                elif subconta.operation_type == 'subtract':
                    total_balance -= subconta.balance
            account.computed_balance = total_balance


class SubContaSequence(models.Model):
    _name = 'sequence.sequence'
    _description = 'Sequência de Subconta'

    name = fields.Char(string='Código', required=True, default='DZ0001')


class SubConta(models.Model):
    _name = 'subconta.subconta'
    _description = 'Subconta'

    account_id = fields.Many2one('account.account', string="Conta Mãe", required=True)
    name = fields.Char(string="Nome do Relatorio", required=True)

    operation_type = fields.Selection([
        ('add', 'Somar'),
        ('subtract', 'Subtrair')
    ], string="Operação", required=True, default='add')

    balance = fields.Float(string="Balance", compute='_compute_balance', store=False)
    item_ids = fields.One2many('subcontaitem.subcontaitem', 'subconta_id', string="Itens da Subconta")

    parent_account_computed_balance = fields.Float(string="Saldo Calculado da Conta Mãe",
                                                   related='account_id.computed_balance', store=False, readonly=True)
    create_date = fields.Datetime(string="Data de Criação", readonly=True)

    code = fields.Char(string="Código")
    order_number = fields.Char(string="Número da Ordem", readonly=True)

    @api.depends('item_ids.amount')
    def _compute_balance(self):
        """Calcula o saldo da subconta com base na soma dos valores dos itens."""
        for record in self:
            record.balance = sum(item.amount for item in record.item_ids)

    @api.onchange('account_id')
    def _onchange_account_id(self):
        """Atualiza o campo code com o código da conta mãe selecionada."""
        if self.account_id:
            self.code = self.account_id.code
        else:
            self.code = ''

    @api.model
    def create(self, vals):
        """Override create method to generate the order_number."""
        if 'order_number' not in vals or vals['order_number'] == False:
            seq_obj = self.env['sequence.sequence']
            sequence = seq_obj.search([], limit=1, order='id desc')
            if sequence:
                # Increment the number
                new_number = int(sequence.name[2:]) + 1
                new_code = 'DZ' + str(new_number).zfill(4)
                vals['order_number'] = new_code
                sequence.name = new_code
            else:
                vals['order_number'] = 'DZ0001'

        return super(SubConta, self).create(vals)


class SubContaItem(models.Model):
    _name = 'subcontaitem.subcontaitem'
    _description = 'Item da Subconta'

    subconta_id = fields.Many2one('subconta.subconta', string="Subconta", required=True)
    account_id = fields.Many2one('account.account', string="Conta Contábil", required=True)
    name = fields.Char(string="Nome do Item", related='account_id.name', store=True, readonly=True)
    amount = fields.Float(string="Valor", required=True)

    @api.onchange('account_id')
    def _onchange_account_id(self):
        """Atualiza o valor do campo 'amount' baseado no saldo da conta selecionada, se aplicável."""
        if self.account_id:
            if hasattr(self.account_id, 'current_balance'):
                self.amount = self.account_id.current_balance or 0.0