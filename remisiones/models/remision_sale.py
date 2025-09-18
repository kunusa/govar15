# -*- coding: utf-8 -*-


from odoo import api, fields, models,_


class RemisionSale(models.Model):
    _inherit = "sale.order"

    message_logistic=fields.Char()
    message_sales=fields.Char()
    message_client=fields.Char()
    message_residence=fields.Char()
    
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
            'view_type': 'form',
            'res_model': 'remision',
            'res_id': remision.id,
            'type': 'ir.actions.act_window',
            'views': [[view_id, 'form']],
        }