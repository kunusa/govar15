# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class StettingsConfig(models.TransientModel):

    """Add options to easily install the submodules"""
    _inherit = 'res.config.settings'

    email_sales = fields.Char(string=' ')


    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('email_sales', self.email_sales or '')

    @api.model
    def get_values(self):
        res = super().get_values()

        
        res.update(
            email_sales=self.env['ir.config_parameter'].sudo().get_param('email_sales', ''),

        )
        return res