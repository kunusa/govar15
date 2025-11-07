# -*- coding: utf-8 -*-

from odoo import models, fields, api



class StockInventory(models.Model):

    _inherit = 'stock.picking'

    @api.onchange('move_ids_without_package')
    def _get_total_op(self):
        for line in self:
            total_qty_done=0.00
            total_to_do=0.00
            if line.move_ids_without_package:
                for lines_id in line.move_ids_without_package:
                        total_qty_done += lines_id.quantity_done
                        total_to_do += lines_id.product_uom_qty

            line.total_qty_done = total_qty_done
            line.total_to_do = total_to_do


    total_qty_done = fields.Float(string = 'Hecho', compute = '_get_total_op')
    total_to_do = fields.Float(string = 'Para ejecutar', compute = '_get_total_op')

class StockMove(models.Model):
    _inherit = 'stock.move'

    categ_id = fields.Many2one(
        'product.category',
        string='Product Category',
        related='product_id.categ_id',
        store=True,
        readonly=True,
        help="Categoria del producto"
    )
    
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        store=True,
        readonly=True,
        help="Unidad de medida del producto"
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
                    stock_string += f"{warehouse.code} -> {available_qty}\n"
                
                rec.stock_popup = stock_string
            else:
                rec.stock_popup = ""