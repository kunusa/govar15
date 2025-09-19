# -*- coding: utf-8 -*-


from odoo import api, fields, models,_


class RemisionSale(models.Model):
    _inherit = "sale.order"

    menssage=fields.Char(compute='_compute_menssage')
    mensage=fields.Char(compute='_compute_menssage')
    bandera=fields.Boolean()
    v_observations=fields.Char(track_visibility='onchange',)
    v_terms=fields.Char(track_visibility='onchange',)
    v_delivery_method=fields.Char(track_visibility='onchange',)
    destiny_so = fields.Char(track_visibility='onchange', string = "Destino")
    message_flag = fields.Boolean()
    sales_flag = fields.Boolean()
    message_logistic=fields.Char()
    message_sales=fields.Char()
    message_client=fields.Char()
    message_residence=fields.Char()
    flag_other_info = fields.Boolean(compute='_compute_other_info')


    @api.depends('invoice_ids', 'invoice_ids.state')
    def _compute_other_info(self):
        for record in self:
            if any(inv.state in ['posted', 'cancel', 'paid'] for inv in record.invoice_ids):
                record.flag_other_info = True
            else:
                record.flag_other_info = False
    
    @api.depends('picking_ids', 'picking_ids.state', 'picking_ids.move_line_ids_without_package')
    def _compute_menssage(self):
        for rec in self:
            varInt = 1
            varOnt = 1
            if rec.picking_ids:
                varInt = 0
                varOnt = 0
            for picking in rec.picking_ids:
                if picking.picking_type_code == 'outgoing':
                    if not picking.move_line_ids_without_package:
                        varInt = 1
                        varOnt = 1
                    for producto in picking.move_line_ids_without_package:
                        if producto.product_qty - producto.qty_done != 0:
                            varInt = 1
                            varOnt = 1
                        if picking.state != 'done' and picking.bandera != True:
                            varInt = 1
                        if picking.bandera != True:
                            varOnt = 1
                                			
            if varOnt == 0:
                varInt = 1

            if varInt == 0:
                rec.menssage = 'Producto surtido'
                rec.bandera = True
            else:
                rec.menssage = ''
                rec.bandera = False
            if varOnt == 0:
                rec.mensage = 'Producto embarcado'
                rec.bandera = True
            else:
                rec.mensage = ''
                if varInt != 0:  # Solo resetear bandera si no se estableció en True arriba
                    rec.bandera = False

    def make_remission(self):

        view_id = self.env.ref('remisiones.view_remisionesgovar_remisiones_from').id
        remision = self.env['remision'].create({
            'partner_id': self.partner_id.id,
            # 'forma_entrega': self.v_delivery_method
        })
        
        for rec in self.order_line:
            self.env['remision_line'].create({
            'id_precotizador': remision.id,
            'producto':rec.product_id.id,
            'cantidad' : rec.product_uom_qty,
            'valor_unitario': rec.price_unit,
            # 'price_list': rec.price_list,
            'importe': rec.price_unit * rec.product_uom_qty,    
            'description': rec.name    
            })           

        return {
            'name': _('Remisión'),
            'view_mode': 'form',
            'res_model': 'remision',
            'res_id': remision.id,
            'type': 'ir.actions.act_window',
            'views': [[view_id, 'form']],
        }