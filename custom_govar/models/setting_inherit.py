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
    email_payment = fields.Char(string=' ')
    email_users = fields.Char(string=' ')
    #Notas de credito
    discount_sale_account = fields.Many2one(comodel_name="account.account", string="Cuenta de descuento sobre venta")
    refaund_sale_account = fields.Many2one(comodel_name="account.account", string="Cuenta de devolución sobre venta")
    discount_purchase_account = fields.Many2one(comodel_name="account.account", string="Cuenta de descuento sobre compra")
    refaund_purchase_account = fields.Many2one(comodel_name="account.account", string="Cuenta de devolución sobre compra")

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('email_product_min', self.email_product_min or '')
        self.env['ir.config_parameter'].sudo().set_param('email_product_min_3', self.email_product_min_3 or '')
        self.env['ir.config_parameter'].sudo().set_param('email_block', self.email_block or '')
        self.env['ir.config_parameter'].sudo().set_param('email_block_all', self.email_block_all or '')
        self.env['ir.config_parameter'].sudo().set_param('email_company', self.email_company or '')
        self.env['ir.config_parameter'].sudo().set_param('email_payment', self.email_payment or '')
        self.env['ir.config_parameter'].sudo().set_param('email_users', self.email_users or '')
        #Notas de credito
        self.env['ir.config_parameter'].sudo().set_param('discount_sale_account', self.discount_sale_account.id if self.discount_sale_account else '')
        self.env['ir.config_parameter'].sudo().set_param('refaund_sale_account', self.refaund_sale_account.id if self.refaund_sale_account else '')
        self.env['ir.config_parameter'].sudo().set_param('discount_purchase_account', self.discount_purchase_account.id if self.discount_purchase_account else '')
        self.env['ir.config_parameter'].sudo().set_param('refaund_purchase_account', self.refaund_purchase_account.id if self.refaund_purchase_account else '')
    @api.model
    def get_values(self):
        res = super().get_values()
        # Get account IDs from config parameters and convert to integers
        discount_sale_account_id = self.env['ir.config_parameter'].sudo().get_param('discount_sale_account', '')
        refaund_sale_account_id = self.env['ir.config_parameter'].sudo().get_param('refaund_sale_account', '')
        discount_purchase_account_id = self.env['ir.config_parameter'].sudo().get_param('discount_purchase_account', '')
        refaund_purchase_account_id = self.env['ir.config_parameter'].sudo().get_param('refaund_purchase_account', '')
        
        res.update(
            email_product_min=self.env['ir.config_parameter'].sudo().get_param('email_product_min', ''),
            email_product_min_3=self.env['ir.config_parameter'].sudo().get_param('email_product_min_3', ''),
            email_block=self.env['ir.config_parameter'].sudo().get_param('email_block', ''),
            email_block_all=self.env['ir.config_parameter'].sudo().get_param('email_block_all', ''),
            email_company=self.env['ir.config_parameter'].sudo().get_param('email_company', ''),
            email_payment=self.env['ir.config_parameter'].sudo().get_param('email_payment', ''),
            email_users=self.env['ir.config_parameter'].sudo().get_param('email_users', ''),
            discount_sale_account=int(discount_sale_account_id) if discount_sale_account_id and discount_sale_account_id.isdigit() else False,
            refaund_sale_account=int(refaund_sale_account_id) if refaund_sale_account_id and refaund_sale_account_id.isdigit() else False,
            discount_purchase_account=int(discount_purchase_account_id) if discount_purchase_account_id and discount_purchase_account_id.isdigit() else False,
            refaund_purchase_account=int(refaund_purchase_account_id) if refaund_purchase_account_id and refaund_purchase_account_id.isdigit() else False,
        )
        return res