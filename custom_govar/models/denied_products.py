# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime ,timedelta
from odoo.exceptions import UserError,ValidationError

class DeniedProducts(models.Model):
	_name = "denied.products"
	_description = "Denied Products"

	name=fields.Many2one(comodel_name='product.template',string='Producto', index=True)
	db_descripcion=fields.Char(string='Producto', related='name.name', store=True)
	dp_code=fields.Char(string='Referencia interna', related='name.default_code', store=True)
	dp_usuario=fields.Many2one(comodel_name='res.users',string='Empleado', index=True)
	dp_cantidad=fields.Integer(string="Cantidad")
	dp_precio=fields.Float(string="Precio")
	dp_fecha=fields.Date(string="Fecha")
	dp_total=fields.Float(string="Total")
	dp_motivo = fields.Char(string= "Motivo")
	dp_desc = fields.Char(string = 'Descrpcion')
	dp_res_partner=fields.Many2one(comodel_name='res.partner',string='Cliente', index=True)
	dp_purchase_order=fields.Many2many('purchase.order','denied_products_rel', 'denied_products_id','purchase_order_id',string='PO')
	


class DeniedProductsSave(models.TransientModel):
	_name = 'denied.product_save'
	_description = "Denied Product Save"
	
	dps_name=fields.Many2one(comodel_name='product.template', required=True, index=True)
	dps_cantidad=fields.Char(required=True)
	motive = fields.Selection([
		('not_inventory', 'Falta de inventario'),
		('price','Precio'),
		('other','Otro')
	], string='Motivo', required= True)
	other_m = fields.Char(string ='Otro')
	dps_res_partner=fields.Many2one(comodel_name= 'res.partner',string='Cliente',required=True, index=True)
	dps_purchase_order=fields.Many2many('purchase.order','denied_products_save_rel', 'denied_products_save_id','denied_purchase_order_id',string='PO')

	def save_denied_products(self):
		motive_desc = ''

		if self.motive == 'not_inventory':
			# Buscar el producto específico
			product = self.env['product.product'].search([('product_tmpl_id', '=', self.dps_name.id)])
			
			# Obtener el almacén del usuario
			warehouse = self.env.user.property_warehouse_id
			
			# Calcular cantidad disponible en el almacén específico
			available_qty = product.with_context(warehouse=warehouse.id).free_qty

			if available_qty >= 1:
				raise ValidationError("Existe material del producto en el almacén")
		if self.motive == 'other':
			if self.other_m == False:
				raise ValidationError("Agreagar la descrpcion de motivo del producto negado")

		motive_desc = self.get_motive()

		fecha=date.today()
		# FIXME cambiar a lista de precios
		preciol3=self.env['product.template'].search([('id','=',self.dps_name.id)]).list_price
		# preciol3=self.env['fixed.prices'].search([('product_id','=',self.dps_name.id),('list_num','=',3)])
		total=0.00
		total=int(self.dps_cantidad)*preciol3
		self.get_pos()

		self.env['denied.products'].create({
			'name':self.dps_name.id,
			'dp_usuario':self.env.user.id,
			'dp_cantidad':int(self.dps_cantidad),
			'dp_precio':preciol3,
			'dp_fecha':fecha,
			'dp_total':total,
			'dp_motivo':motive_desc,
			'dp_desc': self.other_m,
			'dp_res_partner':self.dps_res_partner.id,
			'dp_purchase_order': [(4, order_id.id, None) for order_id in self.dps_purchase_order]
			})


		view_id = self.env.ref('custom_govar.denied_products_save').id

		return {
			'name': _('Deneid Product'),
			'view_mode': 'form',
			'target': 'new',
			'res_model': 'denied.product_save',
			'type': 'ir.actions.act_window',
			'views': [[view_id,'form']],

		}
	
	def save_close(self):
		motive_desc = ''

		if self.motive == 'not_inventory':
			# Buscar el producto específico
			product = self.env['product.product'].search([('product_tmpl_id', '=', self.dps_name.id)])
			
			# Obtener el almacén del usuario
			warehouse = self.env.user.property_warehouse_id
			
			# Calcular cantidad disponible en el almacén específico
			available_qty = product.with_context(warehouse=warehouse.id).free_qty

			if available_qty >= 1:
				raise ValidationError("Existe material del producto en el almacén")
		if self.motive == 'other':
			if self.other_m == False:
				raise ValidationError("Agreagar la descrpcion de motivo del producto negado")

		motive_desc = self.get_motive()

		fecha=date.today()
		# FIXME cambiar a lista de precios
		preciol3=self.env['product.template'].search([('id','=',self.dps_name.id)]).list_price
		# preciol3=self.env['fixed.prices'].search([('product_id','=',self.dps_name.id),('list_num','=',3)])
		total=0.00
		total=int(self.dps_cantidad)*preciol3
		self.get_pos()

		self.env['denied.products'].create({
			'name':self.dps_name.id,
			'dp_usuario':self.env.user.id,
			'dp_cantidad':int(self.dps_cantidad),
			'dp_precio':preciol3,
			'dp_fecha':fecha,
			'dp_total':total,
			'dp_motivo':motive_desc,
			'dp_desc': self.other_m,
			'dp_res_partner':self.dps_res_partner.id,
			'dp_purchase_order': [(4, order_id.id, None) for order_id in self.dps_purchase_order]
			})

	def get_motive(self):
		desc = ''

		if self.motive == 'not_inventory':
			desc= 'Falta de inventario'
		elif self.motive == 'price':
			desc = 'Precio'
		elif self.motive == 'other':
			desc = 'Otro'

		return desc
	
	@api.onchange('dps_name')
	def get_pos(self):

		order_ids = []
		if self.dps_name:
			product = self.env['product.product'].search([('product_tmpl_id','=',self.dps_name.id)])
			query = """SELECT pol.name,pol.qty_received,pol.product_id,pol.product_qty,pol.order_id 
					FROM purchase_order_line as pol
					INNER JOIN purchase_order as po	
					ON pol.order_id = po.id   
					WHERE pol.product_id = {} and po.state != 'cancel' """.format(product.id)
			self.env.cr.execute(query)

			purchase_line_dict = self.env.cr.dictfetchall()

			for line in purchase_line_dict:
				if line.get('product_qty',0)-line.get('qty_received',0) != 0:
					order_ids.append(line.get('order_id'))

		if len(order_ids)>=1:
			self.dps_purchase_order = [(4, order_id, None) for order_id in order_ids]
		

class productTemplateCategory(models.Model):

	_inherit = 'product.template'


	def view_product_denied(self):
		
		view_id = self.env.ref('custom_govar.denied_products_save').id

		context = dict(self._context or {})
		context.update({'default_dps_name': self.id})

		return {
			'name': _('Deneid Product'),
			'view_mode': 'form',
			'target': 'new',
			'res_model': 'denied.product_save',
			'type': 'ir.actions.act_window', 
			'context': context,
			'views': [[view_id,'form']],
		}