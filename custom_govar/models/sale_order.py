# -*- coding: utf-8 -*-
from odoo import models, api, fields



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = "sequence_ref"

    sequence_ref = fields.Integer('No.', compute="_sequence_ref", store = True)
    categ_id = fields.Many2one(
        'product.category',
        string='Product Category',
        related='product_id.categ_id',
        readonly=True,
        help="Categoria del producto"
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unidad de medida',
        related='product_id.uom_id',
        readonly=True,
    )


    stock_popup = fields.Text(string='ST', compute="_get_stock_popup")

    @api.depends('product_id')
    def _get_stock_popup(self):
        for rec in self:
            if rec.product_id:
                stock_string = ""
                warehouse_obj = self.env['stock.warehouse']
                product = rec.product_id
                
                # Buscar almacenes que se muestren en ventas
                warehouse_list = warehouse_obj.search([('view_on_sale', '=', True)])
                
                for warehouse in warehouse_list:
                    # Obtener cantidad disponible en el almacén específico
                    available_qty = product.with_context(warehouse=warehouse.id).qty_available
                    stock_string += f"{warehouse.name} ({warehouse.code}) -> {available_qty}\n"
                
                rec.stock_popup = stock_string
            else:
                rec.stock_popup = ""


    def _prepare_order_line_procurement(self, group_id=False):
        self.ensure_one()
        vals = super(SaleOrderLine, self)._prepare_order_line_procurement(group_id=group_id)
        vals.update({'sequence_ref':self.sequence_ref})
        return vals

    @api.depends('order_id.order_line', 'order_id.order_line.product_id')
    def _sequence_ref(self):
        for line in self:
            no = 0
            for l in line.order_id.order_line:
                no += 1
                l.sequence_ref = no  