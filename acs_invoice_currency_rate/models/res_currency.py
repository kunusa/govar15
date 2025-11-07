# -*- coding: utf-8 -*-

from odoo import models, api


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        use_custom_rate = self._context.get('use_custom_rate')
        custom_rate = self._context.get('custom_rate')
        if use_custom_rate and custom_rate:
            return custom_rate
        else:
            return super(ResCurrency, self)._get_conversion_rate(from_currency, to_currency,  company, date)
