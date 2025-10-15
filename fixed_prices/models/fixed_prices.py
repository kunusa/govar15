# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class fixed_prices(models.Model):
	_name = 'fixed.prices'

	_sql_constraints = [
		('list_uniq', 'UNIQUE (list_num,product_id)',  'No puedes tener listas duplicadas !')
	]

	name = fields.Char(string='Descripcion de la Lista de Precios')
	margin_pctg = fields.Float(string='% Margen',default=35)
	list_num = fields.Integer(string='Lista',index=True)
	price = fields.Float(string='Precio',compute='_compute_price')
	currency_id = fields.Many2one(comodel_name='res.currency',string='Moneda')
	product_id = fields.Many2one(comodel_name='product.template',string='Producto')

	def divzero(self,x,y):
		try:
			return x/y
		except ZeroDivisionError:
			return 0

	@api.onchange('margin_pctg','product_id.currency_fixed_id','product_id.standard_price')
	def _compute_price(self):
		for rec in self:
			# SI NO ES MONEDA LOCAL
			if rec.product_id.currency_fixed_id.name != 'MXN':
				rec.price = (self.divzero(rec.product_id.standard_price,rec.product_id.currency_fixed_id.rate)) * ( 1 + rec.margin_pctg/100)
			else:
				rec.price = rec.product_id.standard_price * ( 1 + rec.margin_pctg/100)



class product_fixed_prices(models.Model):
	_inherit = 'product.template'

	fixed_list_price_ids = fields.One2many(comodel_name='fixed.prices',inverse_name='product_id')
	currency_fixed_id = fields.Many2one(comodel_name='res.currency',string='Moneda de Costo',track_visibility='onchange')

class SalePriceListPartner(models.Model):
	_inherit = 'res.partner'
	
	list_num = fields.Integer(string='Lista',index=True)