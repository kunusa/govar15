from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare




class StatePickingInherit(models.Model):
    _inherit = "stock.picking"

    id_remision=fields.Many2one(inverse_name='pickin_id',comodel_name="remision", string="remicion",invisible=True)

    type_delivered  = fields.Char(string = 'Forma de entrega', compute = '_compute_type_delivered')
    is_remision = fields.Boolean()
    flag_button = fields.Boolean()
    leabe_embarcado=fields.Char(readonly=True, default='Embarcado')
    bandera=fields.Boolean()

    def _compute_type_delivered(self):
        if self.origin:
            if self.origin[:3] == 'REM':
                remission = self.env['remision'].search([('name','=',self.origin)], limit = 1)   
                if len(remission)>=1:
                    self.type_delivered = remission.forma_entrega
            if self.origin[:2] == 'SO':
                origin = self.env['sale.order'].search([('name','=',self.origin)])
                if len(origin)>=1:
                    self.type_delivered = origin.v_delivery_method

    def validate_client(self):

        if self.partner_id.sale_warn == 'block':
            message = self.partner_id.sale_warn_msg
            name = self.partner_id.name
            raise UserError(_(f'Cliente {name} bloqueado \n {message} '))
        if self.state in ['draft','assigned','partially_available']:
            sale_order = self.env['sale.order'].search([('name','=',self.origin)], limit = 1)
            if sale_order:
                if (sale_order.message_logistic == False and sale_order.message_sales == False and sale_order.message_residence == False) and self.origin[:2] == 'SO':
                    raise UserError(_('Se debe indicar si es entegado a paqueteria, entregado a ventas o entregado a domicilio\n para poder validar el pedido'))
        if self.origin:
            if self.origin[:3] == 'REM' and self.picking_type_code == 'outgoing':
                
                remission = self.env['remision'].search([('name','=',self.origin),('state','=','proceso')], limit = 1)
                if remission:
                    remission.state = 'remission'

    def parcial_remision(self):

            if self.state != 'done':
                raise UserError(_('No se puede crear el presupuesto hasta validar la transferencia'))

            remision = self.env['remision'].search([('name','=',self.origin)], limit = 1)

            for line in remision:
                location= self.env['stock.location'].search([('name', '=', 'REMISION'),('usage','=','customer',)])
                outgoing = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('warehouse_id','=',line.default_warehouse.id,)])
                picking = self.env['stock.picking'].create({
                    'partner_id':line.partner_id.id,
                    'origin':line.name,
                    'picking_type_id':outgoing[0].id,
                    'location_id':location.id,
                    'location_dest_id':line.default_warehouse.lot_stock_id.id,
                    'id_remision':line.id,
                    })
                for rec in line.remisiones_line_id:
                    producto = self.env['product.product'].search([('product_tmpl_id', '=', rec.producto.id)])
                    self.env['stock.move'].create({
                        'product_id':producto.id,
                        'product_uom_qty':rec.cantidad,
                        'product_uom':rec.unidad_medida.id,
                        'picking_id':picking.id,
                        'location_id':location.id,
                        'name':"["+producto.default_code+"] "+producto.product_tmpl_id.name,
                        'location_dest_id':line.default_warehouse.lot_stock_id.id,
                        })
                picking.action_confirm()
                picking.action_assign()
                for x in picking.move_line_ids_without_package:
                    x.qty_done=x.product_qty
                picking.button_validate()
                iva=self.env['account.tax'].search([('type_tax_use','=','sale'),('name','=','IVA(16%) VENTAS',)])            
                sale = self.env['sale.order'].create({
                    'partner_id':line.partner_id.id,
                    'payment_term_id':line.partner_id.property_payment_term_id.id,
                    'warehouse_id':line.default_warehouse.id,
                    'user_id':line.partner_id.user_id.id,
                    'picking_policy':'direct',
                    'client_order_ref':line.clave_de_cliente,
                    'v_observations':line.observaciones,
                    'v_delivery_method':line.forma_entrega,
                    'v_terms':line.condiciones,
                    'origin':line.name,
                })
                line.write({'id_sale':sale.id})
                for rec in line.remisiones_line_id:
                    producto = self.env['product.product'].search([('product_tmpl_id', '=', rec.producto.id)])
                    self.env['sale.order.line'].create({
                        'product_id':producto.id,
                        'product_uom_qty':rec.cantidad,
                        'price_unit':rec.valor_unitario,
                        'tax_id':[(6,0,[iva.id])],
                        'price_list':rec.price_list,
                        'order_id':sale.id,
                        'name':"["+producto.default_code+"] "+producto.product_tmpl_id.name,
                        })
                line.state='done'

            remision.update({
                'message_remission': 'Remision parcial'
            })
            self.update({
                'is_remision': False,
            })


    def button_validate(self):
        self.validate_client()

        rec = super().button_validate()

        self.close_so()

        return rec


    def close_so(self):
        qty_done = 0
        qty_origin = 0

        if 'Devoluciones' in self.picking_type_id.name and self.picking_type_id.code == 'incoming':
            for line in self.move_line_ids_without_package:
                qty_done += line.qty_done

            origin_picking = self.env['stock.picking'].search([('name','=',self.origin)], limit = 1)


            if origin_picking.origin[:2] == 'SO':
                origin_doc = self.env['sale.order'].search([('name','=',origin_picking.origin)], limit = 1)
            
                for line_so in origin_doc.order_line:
                    qty_origin += line_so.product_uom_qty

                if qty_done == qty_origin:
                    query = """UPDATE sale_order set state = 'close', invoice_status = 'no' where id = {}""".format(origin_doc.id)
                    self.env.cr.execute(query)

            elif origin_picking.origin[:3] == 'REM':
                origin_rem = self.env['remisionesgovar.remisiones'].search([('name','=',origin_picking.origin)], limit = 1)

                for line_so in origin_rem.remisiones_line_id:
                    qty_origin += line_so.cantidad

                if qty_done == qty_origin:
                    query = """UPDATE remisionesgovar_remisiones set state = 'closed' where id = {}""".format(origin_rem.id)
                    self.env.cr.execute(query)


    def write_message_rem(self,message):

        if self.origin:
            if self.origin[:3] == 'REM':
                remission = self.env['remision'].search([('name','=',self.origin)], limit = 1)
                if len(remission)>=1:
                    remission.message_logistic = message
                    remission.sales_flag = True
                    self.flag_button = True

            if self.origin[:2] == 'SO':
                sale_order = self.env['sale.order'].search([('name','=',self.origin)], limit = 1)
                if len(sale_order)>=1:
                    sale_order.message_logistic = message
                    self.flag_button = True
                    sale_order.sales_flag = True

    def delivered_logistic(self):
        self.write_message_rem('Surtido paqueteria')

    def delivered_sales(self):
        self.write_message_rem('Surtido mostrador')


    def delivered_residence(self):
        self.write_message_rem('Surtido domicilio')
