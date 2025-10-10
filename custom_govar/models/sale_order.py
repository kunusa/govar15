# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.tools import float_compare


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
                    stock_string += f"{warehouse.code} -> {available_qty}\n"
                
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

    @api.onchange('product_uom_qty', 'product_uom')
    def _onchange_product_id_check_availability(self):
        
        if not self.product_id or not self.product_uom_qty or not self.product_uom:
            return {}

        if self.env.user.company_id.message_stock == False and not self.user_has_groups('custom_govar.avoid_message_stock'):
            if self.product_id.type == 'product':
                precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                product_qty = self.product_uom._compute_quantity(self.product_uom_qty, self.product_id.uom_id)
                if float_compare(self.product_id.virtual_available, product_qty, precision_digits=precision) == -1:
                    # Check if product is Make To Order (MTO) - if so, no warning needed
                    if not self._is_mto_route():
                        warning_mess = {
                            'title': _('¡No hay suficiente inventario!'),
                            'message': _('Usted planea vender %s %s pero solo tiene %s %s disponible!\nEl stock disponible es %s %s. ') % \
                                (self.product_uom_qty, self.product_uom.name, self.product_id.virtual_available, self.product_id.uom_id.name, self.product_id.qty_available, self.product_id.uom_id.name)
                        }
                        return {'warning': warning_mess}
        return {}

    def _is_mto_route(self):
        """
        Check if the product is configured for Make To Order (MTO) route.
        If it's MTO, no stock warning should be shown.
        """
        self.ensure_one()
        if not self.product_id or not self.order_id.warehouse_id:
            return False
            
        # Get product routes
        product_routes = self.route_id or (self.product_id.route_ids + self.product_id.categ_id.total_route_ids)
        
        # Check MTO route
        mto_route = self.order_id.warehouse_id.mto_pull_id.route_id
        if not mto_route:
            try:
                mto_route = self.env['stock.warehouse']._find_global_route('stock.route_warehouse0_mto', _('Make To Order'))
            except:
                # If MTO route not found, treat as MTS (Make To Stock)
                return False
        
        # Return True if MTO route is in product routes
        return mto_route and mto_route in product_routes