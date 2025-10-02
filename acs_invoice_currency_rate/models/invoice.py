# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('currency_id', 'company_id.currency_id')
    def _compute_not_company_currency(self):
        for rec in self:
            rec.not_company_currency = rec.currency_id and rec.currency_id != rec.company_id.currency_id

    @api.depends('currency_id', 'not_company_currency', 'use_custom_rate', 'invoice_date')
    def _compute_currency_rate(self):
        for rec in self:
            rate = rec.currency_id.with_context(data=rec.invoice_date).rate
            rec.currency_rate = 1 / (rate or rec.currency_id.rate)

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'custom_rate','use_custom_rate')
    def _compute_amount(self):
        for move in self:
            super(AccountMove, move.with_context(
                use_custom_rate=move.use_custom_rate,
                custom_rate=move.custom_rate))._compute_amount()

    @api.depends('amount_total', 'custom_rate')
    def _compute_amount_total_company_currency(self):
        for rec in self:
            if rec.not_company_currency:
                rec.amount_total_company_currency = rec.amount_residual  * rec.custom_rate
            else:
                rec.amount_total_company_currency = rec.amount_total

    not_company_currency = fields.Boolean('TC Definido Por Usuario', compute='_compute_not_company_currency')
    currency_rate = fields.Float(string='TC Sistema',compute='_compute_currency_rate',
        digits=(12, 6), readonly=True, store=True, help="Tipo de cambio de esta Factura")
    use_custom_rate = fields.Boolean('TC Usuario', readonly=True, 
        states={'draft': [('readonly', False)]})
    custom_rate = fields.Float(string='TC Usuario', digits=(12, 6))
    #amount_residual_signed canbe used insted but it will have minus sign in vendor bill so added new field
    amount_total_company_currency = fields.Float(string="Cantidad en Moneda de la Empresa",
        compute='_compute_amount_total_company_currency')

    def _inverse_amount_total(self):
        for move in self:
            super(AccountMove, move.with_context(
                use_custom_rate=move.use_custom_rate,
                custom_rate=move.custom_rate))._inverse_amount_total()

    @api.onchange('date', 'currency_id', 'use_custom_rate')
    def _onchange_currency(self):
        if self.env.context.get('default_custom_rate'):
            self.custom_rate = self.env.context.get('default_custom_rate')
        else:
            self.custom_rate = 1 / self.currency_id.with_context(data=self.invoice_date).rate

        super(AccountMove, self.with_context(
                use_custom_rate=self.use_custom_rate,
                custom_rate=self.custom_rate))._onchange_currency()

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if not self.use_custom_rate and self.journal_id:
            self.currency_id = self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id

    @api.onchange('custom_rate')
    def onchange_custom_rate(self):
        self.invoice_line_ids._onchange_price_subtotal()
        self._recompute_dynamic_lines(recompute_all_taxes=True)

    def _recompute_tax_lines(self, recompute_tax_base_amount=False,tax_rep_lines_to_recompute=None):
        super(AccountMove, self.with_context(
            use_custom_rate=self.use_custom_rate,
            custom_rate=self.custom_rate))._recompute_tax_lines(recompute_tax_base_amount=recompute_tax_base_amount)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    use_custom_rate = fields.Boolean(related="move_id.use_custom_rate", string='Use Custom Rate')
    custom_rate = fields.Float(related="move_id.custom_rate", string='Custom Rate')

    @api.depends('debit', 'credit', 'account_id', 'amount_currency', 'currency_id', 'matched_debit_ids', 'matched_credit_ids', 'matched_debit_ids.amount', 'matched_credit_ids.amount', 'move_id.state', 'company_id','move_id.custom_rate','move_id.use_custom_rate')
    def _amount_residual(self):
        for line in self:
            super(AccountMoveLine, line.with_context(
                use_custom_rate=line.move_id.use_custom_rate,
                custom_rate=line.move_id.custom_rate))._amount_residual()

    @api.onchange('quantity', 'discount', 'price_unit', 'tax_ids', 'custom_rate', 'use_custom_rate')
    def _onchange_price_subtotal(self):
        super(AccountMoveLine, self.with_context(
                use_custom_rate=self.move_id.use_custom_rate,
                custom_rate=self.move_id.custom_rate))._onchange_price_subtotal()

    @api.onchange('currency_id', 'custom_rate', 'use_custom_rate')
    def _onchange_currency(self):
        super(AccountMoveLine, self.with_context(
            use_custom_rate=self.move_id.use_custom_rate,
            custom_rate=self.move_id.custom_rate))._onchange_currency()

    def _get_computed_price_unit(self):
        return super(AccountMoveLine, self.with_context(
            use_custom_rate=self.use_custom_rate,
            custom_rate=self.custom_rate))._get_computed_price_unit()
