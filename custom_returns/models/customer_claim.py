# -*- coding: utf-8 -*-

from odoo import models, fields, api

class cusomer_claim(models.Model):
    _name = 'customer.claim'

    name = fields.Char(string="Folio")
    invoice_id =fields.Many2one(comodel_name='account.invoice',string='Factura')
    product_id=fields.Many2one(string="Producto",comodel_name='product.product')
    quantity_invoice = fields.Float(string= "Cantidad factura")
    quantity = fields.Float(string="Cantidad")
    web_claim_id=fields.Many2one(inverse_name='web_main_id',comodel_name="website.support.ticket", string="Reclamo",invisible=True)
    price_unit = fields.Float(string= "Precio")