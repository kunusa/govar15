# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class StettingsConfig(models.TransientModel):

    """Add options to easily install the submodules"""
    _inherit = 'res.config.settings'

    email_product_min = fields.Char(string='Envio de correo')
    email_product_min_3 = fields.Char(string='Envio de correo')
    email_block = fields.Char(string=' ')
    email_block_all = fields.Char(string=' ')
    email_company = fields.Char(string=' ')

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('email_product_min', self.email_product_min or '')
        self.env['ir.config_parameter'].sudo().set_param('email_product_min_3', self.email_product_min_3 or '')
        self.env['ir.config_parameter'].sudo().set_param('email_block', self.email_block or '')
        self.env['ir.config_parameter'].sudo().set_param('email_block_all', self.email_block_all or '')
        self.env['ir.config_parameter'].sudo().set_param('email_company', self.email_company or '')
    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            email_product_min=self.env['ir.config_parameter'].sudo().get_param('email_product_min', ''),
            email_product_min_3=self.env['ir.config_parameter'].sudo().get_param('email_product_min_3', ''),
            email_block=self.env['ir.config_parameter'].sudo().get_param('email_block', ''),
            email_block_all=self.env['ir.config_parameter'].sudo().get_param('email_block_all', ''),
            email_company=self.env['ir.config_parameter'].sudo().get_param('email_company', ''),
        )
        return res