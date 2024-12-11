from odoo import models, fields, api

class Relatorio(models.Model):
    _name = 'relatorio.relatorio'
    _description = 'Relatório'

    name = fields.Char(string="Nome do Relatório", required=True)
    descricao = fields.Text(string="Descrição")
    subconta_ids = fields.Many2many('subconta.subconta', 'relatorio_id', string="Subcontas")
    total_balance = fields.Float(string="Saldo Total", compute='_compute_total_balance', store=False)
    create_date = fields.Datetime(string="Data de Criação", readonly=True)
    order_number = fields.Char(string="Número da Ordem", readonly=True)
    company_id = fields.Many2one('res.company', string="Companhia", default=lambda self: self.env.company,
                                 readonly=True)

    @api.depends('subconta_ids.saldo', 'subconta_ids.operation_type')
    def _compute_total_balance(self):
        """Calcula o saldo total do relatório considerando o tipo de operação de cada subconta."""
        for record in self:
            total = 0.0
            for subconta in record.subconta_ids:
                if subconta.operation_type == 'add':
                    total += subconta.saldo
                elif subconta.operation_type == 'subtract':
                    total -= subconta.saldo
            record.total_balance = total

    @api.model
    def create(self, vals):
        """Override create method to generate the order_number."""
        if 'order_number' not in vals or vals['order_number'] == False:
            seq_obj = self.env['sequence.sequence']
            sequence = seq_obj.search([], limit=1, order='id desc')
            if sequence:

                new_number = int(sequence.name[2:]) + 1
                new_code = 'DRE' + str(new_number).zfill(4)
                vals['order_number'] = new_code
                sequence.name = new_code
            else:
                vals['order_number'] = 'DRE0001'

        return super(Relatorio, self).create(vals)

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
    relatorio_id = fields.Many2one('relatorio.relatorio', string="Relatório")
    name = fields.Char(string="Nome da Subconta", required=True)

    operation_type = fields.Selection([
        ('add', 'Somar'),
        ('subtract', 'Subtrair')
    ], string="Operação", required=True, default='add')

    balance = fields.Float(string="Balance", compute='_compute_balance', store=False)
    item_ids = fields.One2many('subcontaitem.subcontaitem', 'subconta_id', string="Itens da Subconta")

    parent_account_computed_balance = fields.Float(string="Saldo Calculado da Conta Mãe",
                                                   related='account_id.computed_balance', store=True, readonly=True)
    create_date = fields.Datetime(string="Data de Criação", readonly=True)

    code = fields.Char(string="Código")

    saldo = fields.Float(string="Balance", compute='_compute_saldo', store=False)

    start_date = fields.Date(string="Data de Início")
    end_date = fields.Date(string="Data de Fim")

    saved = fields.Boolean(string="Saved", default=False)


    @api.model
    def create(self, vals):

        vals['saved'] = True
        record = super(SubConta, self).create(vals)
        return record

    def write(self, vals):

        if 'saved' not in vals and not self.saved:
            vals['saved'] = True
        return super(SubConta, self).write(vals)

    @api.depends('item_ids.amount')
    def _compute_balance(self):
        """Calcula o saldo da subconta com base na soma dos valores dos itens."""
        for record in self:
            record.balance = sum(item.amount for item in record.item_ids)

    @api.onchange('account_id')
    def _onchange_account_code(self):
        """Atualiza o código da subconta com o código da conta mãe selecionada."""
        if self.account_id:
            self.code = self.account_id.code
        else:
            self.code = False

    @api.depends('account_id', 'start_date', 'end_date')
    def _compute_saldo(self):
        """Calcula o saldo da conta mãe considerando o intervalo de datas."""
        for record in self:
            if record.account_id and record.start_date and record.end_date:
                current_balance = record._calculate_current_balance(record.account_id, record.start_date,
                                                                    record.end_date)
                record.saldo = current_balance + record.balance
            else:
                record.saldo = 0.0

    @api.onchange('account_id', 'start_date', 'end_date')
    def _onchange_account_id(self):
        """Calcula o saldo da conta mãe considerando as datas."""
        self._compute_saldo()

    def _calculate_current_balance(self, account, start_date, end_date):
        """Calcula o current_balance da conta mãe dentro do intervalo de datas."""
        transactions = self.env['account.move.line'].search([
            ('account_id', '=', account.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date)
        ])

        total_balance = 0
        for trans in transactions:

            total_balance += trans.balance

        return total_balance


class SubContaItem(models.Model):
    _name = 'subcontaitem.subcontaitem'
    _description = 'Item da Subconta'

    subconta_id = fields.Many2one('subconta.subconta', string="Subconta", required=True)
    account_id = fields.Many2one('account.account', string="Conta Contábil", required=True)
    name = fields.Char(string="Nome do Item", related='account_id.name', store=True, readonly=True)
    amount = fields.Float(string="Valor", required=True)
    create_date = fields.Datetime(string="Data de Criação", readonly=True)

    @api.onchange('account_id')
    def _onchange_account_id(self):
        """Atualiza o valor do campo 'amount' baseado no saldo da conta selecionada e nas datas da subconta."""
        if self.account_id and self.subconta_id:
            start_date = self.subconta_id.start_date
            end_date = self.subconta_id.end_date

            if start_date and end_date:
                transactions = self.env['account.move.line'].search([
                    ('account_id', '=', self.account_id.id),
                    ('date', '>=', start_date),
                    ('date', '<=', end_date)
                ])

                self.amount = sum(trans.balance for trans in transactions) or 0.0
            else:
                self.amount = self.account_id.current_balance if hasattr(self.account_id, 'current_balance') else 0.0



