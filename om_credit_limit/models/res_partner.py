from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    amount_credit_limit = fields.Monetary(string='Límite de crédito interno', default=-1)
    credit_limit_compute = fields.Monetary(
        string='Límite de crédito', default=-1,
        compute='_compute_credit_limit_compute', inverse='_inverse_credit_limit_compute',
        help='Un límite de cero significa que no hay límite. Un límite de -1 utilizará el límite predeterminado de la compañía).'
    )
    show_credit_limit = fields.Boolean(compute='_compute_show_credit_limit')

    @api.depends('amount_credit_limit')
    @api.depends_context('company')
    def _compute_credit_limit_compute(self):
        for partner in self:
            partner.credit_limit_compute = self.env.company.account_default_credit_limit if partner.amount_credit_limit == -1 else partner.amount_credit_limit

    @api.depends('credit_limit_compute')
    @api.depends_context('company')
    def _inverse_credit_limit_compute(self):
        for partner in self:
            is_default = partner.credit_limit_compute == self.env.company.account_default_credit_limit
            partner.amount_credit_limit = -1 if is_default else partner.credit_limit_compute

    @api.depends_context('company')
    def _compute_show_credit_limit(self):
        for partner in self:
            partner.show_credit_limit = self.env.company.account_credit_limit

    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + ['amount_credit_limit']
