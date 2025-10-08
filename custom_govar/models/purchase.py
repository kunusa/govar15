# -*- coding: utf-8 -*-

from odoo import models, fields, api

		
class SequencePurchaseOrderLine(models.Model):
	_inherit ='purchase.order.line'
	_order = "sequence_ref"

	sequence_ref = fields.Integer('No.', compute="_sequence_ref")

	def _prepare_order_line_procurement(self, group_id=False):
		self.ensure_one()
		vals = super(SequencePurchaseOrderLine, self)._prepare_order_line_procurement(group_id=group_id)
		vals.update({'sequence_ref':self.sequence_ref})
		return vals

	@api.depends('order_id.order_line', 'order_id.order_line.product_id')
	def _sequence_ref(self):

		for line in self:
			no = 0
			for l in line.order_id.order_line:
				no += 1
				l.sequence_ref = no  

