from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    account_credit_limit = fields.Boolean(
        string="Límite de crédito de ventas", related="company_id.account_credit_limit", readonly=False,
        help="Habilitar límite de crédito para la empresa actual.")
    account_default_credit_limit = fields.Monetary(
        string="Límite de crédito predeterminado", related="company_id.account_default_credit_limit", readonly=False,
        help="Un límite de cero significa que no hay límite por defecto.")
    credit_limit_type = fields.Selection(string="Tipo de límite de crédito", related="company_id.credit_limit_type",
                                         readonly=False)