import time
from datetime import date
from datetime import timedelta, datetime
from odoo import fields, models, api, _
import io
import json
from odoo.exceptions import AccessError, UserError, AccessDenied

try:
    from odoo.tools.misc import xlsxwriter, formatLang
except ImportError:
    import xlsxwriter


class AgeingView(models.TransientModel):
    _name = 'day_book.day_book'

    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True,
                                 default=lambda self: self.env.company)
    journal_ids = fields.Many2many('account.journal', string='Journals',
                                   required=True,
                                   default=lambda self: self.env[
                                       'account.journal'].search([]))

    account_ids = fields.Many2many('account.account',
                                   required=True, string='Accounts',
                                   )

    date_from = fields.Date(string='Start Date', default=date.today(),
                            required=True)

    date_to = fields.Date(string='End Date', default=date.today(),
                          required=True)

    saldo_inicial = fields.Float(string="Saldo Inicial", compute='_compute_initial_balance',
                                 store=True)

    saldo_final = fields.Float(string="Saldo Final", compute="_compute_saldo_final", store=True)

    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves', required=True,
                                   default='posted')
    @api.model
    def view_report(self, option):
        r = self.env['day_book.day_book'].search([('id', '=', option[0])])
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = \
            r.read(['date_from', 'date_to', 'journal_ids', 'target_move',
                    'account_ids'])[0]
        filters = self.get_filter(option)
        records = self._get_report_values(data)
        currency = self._get_currency()

        print(currency)



        print(records['initial_balance'])
        print(records['final_balance'])



        return {
            'name': "Day Book",
            'type': 'ir.actions.client',
            'tag': 'd_d',
            'filters': filters,
            'report_lines': records['Accounts'],
            'initial_balance': records['initial_balance'],
            'final_balance': records['final_balance'],
            'currency': currency,
        }


    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}

        if data.get('target_move'):
            filters['target_move'] = data.get('target_move')
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to'):
            filters['date_to'] = data.get('date_to')
        if data.get('journal_ids'):
            filters['journals'] = self.env['account.journal'].browse(
                data.get('journal_ids')).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(
                data.get('account_ids', [])).mapped('code')
        else:
            filters['accounts'] = ['All']
        filters['company_id'] = ''
        filters['accounts_list'] = data.get('accounts_list')
        filters['journals_list'] = data.get('journals_list')
        filters['company_name'] = data.get('company_name')
        filters['target_move'] = data.get('target_move').capitalize()

        return filters

    def get_filter_data(self, option):
        r = self.env['day_book.day_book'].search([('id', '=', option[0])])
        default_filters = {}
        company_id = self.env.companies
        company_domain = [('company_id', 'in', company_id.ids)]

        journal_ids = self.journal_ids if self.journal_ids else self.env['account.journal'].search(company_domain,
                                                                                                   order="company_id, name")

        # Filtrar apenas as contas do tipo 'receivable' e 'payable'
        accounts_ids = self.account_ids if self.account_ids else self.env['account.account'].search([

            ('company_id', 'in', company_id.ids)
        ], order="company_id, name")

        # Aqui, vamos filtrar apenas os diários que possuem o nome 'Bank'
        bank_journal_ids = self.env['account.journal'].search([('type', '=', 'bank')])

        journals = []
        o_company = False
        for j in bank_journal_ids:
            if j.company_id != o_company:
                journals.append(('divider', j.company_id.name))
                o_company = j.company_id
            journals.append((j.id, j.name, j.code))

        accounts = []
        o_company = False
        for j in accounts_ids:
            if j.company_id != o_company:
                accounts.append(('divider', j.company_id.name))
                o_company = j.company_id
            accounts.append((j.id, j.name))

        filter_dict = {
            'journal_ids': self.journal_ids.ids,
            'account_ids': self.account_ids.ids,
            'company_id': company_id.ids,
            'date_from': r.date_from,
            'date_to': r.date_to,
            'target_move': str(r.target_move).capitalize(),
            'journals_list': journals,
            'accounts_list': accounts,
            'company_name': ', '.join(self.env.companies.mapped('name')),
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_initial_balance(self, journals, date_start):
        initial_balance = 0
        for journal in journals:
            account_moves = self.env['account.move.line'].search([
                ('account_id', '=', journal.default_account_id.id),
                ('journal_id', '=', journal.id),
                ('date', '<', date_start)
            ])

            for move in account_moves:
                initial_balance += move.debit - move.credit
        return initial_balance

    def _get_transaction_balance(self, transaction_data, initial_balance, transaction_date, is_last_day=False):
        transaction_balance = transaction_data.get('balance', 0)

        if isinstance(transaction_date, str):
            transaction_date = fields.Datetime.from_string(transaction_date).date()
        date_str = transaction_date.strftime('%Y-%m-%d')

        print('Balanco do dia :', transaction_balance)
        final_saldo = initial_balance + transaction_balance
        self.saldo_final = final_saldo

        if is_last_day:
            print(f"Saldo final do último dia: {final_saldo}")

        return {
            'transaction_balance': transaction_balance,
            'final_balance': final_saldo,
            'transaction_date': transaction_date
        }

    def _get_report_values(self, data=None):
        form_data = data['form']
        active_acc = data['form']['account_ids']
        accounts = self.env['account.account'].search([('id', 'in', active_acc)]) if data['form']['account_ids'] else \
        self.env['account.account'].search([])
        if not accounts:
            raise UserError(_("No Accounts Found! Please Add One"))
        active_jrnl = data['form']['journal_ids']
        journals = self.env['account.journal'].search([('id', 'in', active_jrnl)]) if data['form']['journal_ids'] else \
        self.env['account.journal'].search([])
        if not journals:
            raise UserError(_("No journals Found!"))

        date_start = datetime.strptime(str(form_data['date_from']), '%Y-%m-%d').date()
        date_end = datetime.strptime(str(form_data['date_to']), '%Y-%m-%d').date()
        days = (date_end - date_start).days
        dates = []
        record = []

        initial_balance = self._get_initial_balance(journals, date_start)
        self.saldo_inicial = initial_balance

        final_balance_last_day = initial_balance

        for i in range(days + 1):
            current_date = date_start + timedelta(days=i)
            pass_date = str(current_date)

            accounts_res = self._get_account_move_entry(accounts, form_data, journals, pass_date)
            if accounts_res['lines']:
                if not record:
                    saldo_anterior = initial_balance
                else:
                    saldo_anterior = record[-1]['balance']

                record.append({
                    'date': current_date,
                    'debit': accounts_res['debit'],
                    'credit': accounts_res['credit'],
                    'balance': saldo_anterior + accounts_res['balance'],
                    'child_lines': accounts_res['lines'],
                    'id': accounts_res['move_id'],
                })
                saldo_anterior = record[-1]['balance']


        return {
            'doc_ids': self.ids,
            'time': time,
            'initial_balance': initial_balance,
            'Accounts': record,
            'final_balance':  record[-1]['balance'],

        }

    @api.depends('journal_ids', 'date_from')
    def _compute_initial_balance(self):
        for record in self:
            journals = record.journal_ids
            date_start = record.date_from
            record.saldo_inicial = self._get_initial_balance(journals, date_start)

    @api.model
    def create(self, vals):
        vals['target_move'] = 'posted'
        res = super(AgeingView, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('target_move'):
            vals.update({'target_move': vals.get('target_move').lower()})
        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(6, 0, vals.get('journal_ids'))]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})
        if vals.get('account_ids'):
            vals.update(
                {'account_ids': [(4, j) for j in vals.get('account_ids')]})
        if vals.get('account_ids') == []:
            vals.update({'account_ids': [(5,)]})
        res = super(AgeingView, self).write(vals)
        return res

    def _get_account_move_entry(self, accounts, form_data, journals, pass_date):
        cr = self.env.cr
        move_line = self.env['account.move.line']
        tables, where_clause, where_params = move_line._query_get()
        wheres = [""]
        companies = self.env.companies.ids
        companies.append(0)
        target_move = "AND l.company_id in %s" % str(tuple(companies))
        if where_clause.strip():
            wheres.append(where_clause.strip())
        if form_data['target_move'] == 'posted':
            target_move += " AND m.state = 'posted'"
        else:
            target_move += """AND m.state in ('draft','posted') """
        sql = ('''
                SELECT l.id AS lid,m.id AS move_id, acc.name as accname, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, 
                l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, 
                COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,
                m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                JOIN account_account acc ON (l.account_id = acc.id) 
                WHERE l.account_id IN %s AND l.journal_id IN %s ''' + target_move + ''' AND l.date = %s
                GROUP BY l.id,m.id, l.account_id, l.date,
                     j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name , acc.name
                     ORDER BY l.date DESC
        ''')
        params = (
            tuple(accounts.ids), tuple(journals.ids), pass_date)
        cr.execute(sql, params)
        data = cr.dictfetchall()

        res = {}
        debit = credit = balance = 0.00
        id = ''
        for line in data:
            debit += line['debit']
            credit += line['credit']
            balance += line['balance']
            id = line['move_id']
        res['debit'] = debit
        res['credit'] = credit
        res['balance'] = balance
        res['lines'] = data
        res['move_id'] = id
        return res

    @api.model
    def _get_currency(self):
        journal = self.env['account.journal'].browse(
            self.env.context.get('default_journal_id', False))
        if journal.currency_id:
            return journal.currency_id.id
        lang = self.env.user.lang
        if not lang:
            lang = 'en_US'
        lang = lang.replace("_", '-')
        currency_array = [self.env.company.currency_id.symbol,
                          self.env.company.currency_id.position, lang]
        return currency_array

    def get_dynamic_xlsx_report(self, data, response, report_data, dfr_data):
        report_data_main = json.loads(report_data)
        output = io.BytesIO()
        filters = json.loads(data)
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_l = workbook.add_format(
            {'font_size': '10px', 'border': 1, 'bold': True})
        sheet.merge_range('A2:D3',
                          filters.get('company_name') + ':' + ' Day Book',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})
        if filters.get('date_from'):
            sheet.merge_range('A4:B4', 'From: ' + filters.get('date_from'),
                              date_head)
        if filters.get('date_to'):
            sheet.merge_range('C4:D4', 'To: ' + filters.get('date_to'),
                              date_head)
        sheet.write('A5', 'Journals: ' + ', '.join([lt or '' for lt in
                                                    filters[
                                                        'journals']]),
                    date_head)

        sheet.merge_range('E4:F4',
                          'Target Moves: ' + filters.get('target_move'),
                          date_head)
        sheet.merge_range('B5:D5',
                          'Account Type: ' + ', '.join([lt or '' for lt in
                                                        filters[
                                                            'accounts']]),
                          date_head)

        sheet.merge_range('A7:E7', 'Date', sub_heading)
        sheet.write('F7', 'Debit', sub_heading)
        sheet.write('G7', 'Credit', sub_heading)
        sheet.write('H7', 'Balance', sub_heading)

        row = 6
        col = 0
        sheet.set_column(4, 0, 15)
        sheet.set_column(5, 0, 15)
        sheet.set_column(6, 1, 15)
        sheet.set_column(7, 2, 15)
        sheet.set_column(8, 3, 15)
        sheet.set_column(9, 4, 15)
        sheet.set_column(10, 5, 15)
        sheet.set_column(11, 6, 15)
        for rec_data in report_data_main:
            one_lst = []
            two_lst = []
            row += 1
            sheet.merge_range(row, col, row, col + 4, rec_data['date'], txt_l)
            sheet.write(row, col + 5, rec_data['debit'], txt_l)
            sheet.write(row, col + 6, rec_data['credit'], txt_l)
            sheet.write(row, col + 7, rec_data['balance'], txt_l)
            for line_data in rec_data['child_lines']:
                row += 1
                sheet.write(row, col, line_data.get('ldate'), txt)
                sheet.write(row, col + 1, line_data.get('lcode'), txt)
                sheet.write(row, col + 2, line_data.get('partner_name'),txt)
                sheet.write(row, col + 3, line_data.get('move_name'),txt)
                sheet.write(row, col + 4, line_data.get('lname'),txt)
                sheet.write(row, col + 5, line_data.get('debit'),txt)
                sheet.write(row, col + 6, line_data.get('credit'),txt)
                sheet.write(row, col + 7, line_data.get('balance'),txt)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()