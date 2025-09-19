


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class accountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    remision_id = fields.Many2one(comodel_name='remision', string= 'Remision')
    origin = fields.Char(string= 'Origen')

class productTemplateInherit(models.Model):
    _inherit = 'account.move'

    remision_ids = fields.Many2many(comodel_name='remision', string= 'Remisiones')
    document_origin = fields.Char(string= 'Documento origen')
    other_observations=fields.Char(string= 'Observaciones',compute='_fill_fields')
    other_delivery_method=fields.Char(readonly=True)
    other_terms=fields.Char(readonly=True)
    pedido_cliente=fields.Char(string= 'Pedido del cliente',track_visibility='onchange')
    package = fields.Char(string = 'Paqueteria',track_visibility='onchange')
    destination_invoice = fields.Char(string= 'Destino')

    @api.model
    def create(self, vals):
        # Si no se proporciona document_origin, intentar obtenerlo de diferentes fuentes
        if self.env.context.get('active_model') == 'sale.order' and self.env.context.get('active_id'):
            sale_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
            vals['document_origin'] = sale_order.name
        else:
            sale_order = False
        rec = super().create(vals)
        rec.get_other_info(sale_order)

        return rec

    def get_other_info(self, sale_order = False):

        if self.document_origin and self.move_type == 'out_invoice':
            if self.document_origin[:1] == 'S' and sale_order:
                self.destination_invoice=sale_order.destiny_so
                self.pedido_cliente=sale_order.client_order_ref
                self.other_delivery_method=sale_order.v_delivery_method
                self.other_terms=sale_order.v_terms
                self.pedido_cliente = sale_order.client_order_ref
            elif self.document_origin[:3] == 'REM':
                rem =self.env['remision'].search([('name','=',self.document_origin)])
                self.other_observations=rem.observaciones
                self.other_delivery_method=rem.forma_entrega
                self.other_terms=rem.condiciones
                self.pedido_cliente = rem.pedido_cliente
                self.package = rem.package
                self.destination_invoice=rem.destiny

    @api.depends('document_origin')
    def _fill_fields(self):
        for record in self:
            if record.document_origin:
                if record.document_origin[:1] == 'S':
                    SaleOrder = self.env['sale.order'].search([('name', '=', record.document_origin)], limit=1)
                    if SaleOrder:
                        record.other_observations = SaleOrder.v_observations
                        record.other_delivery_method = SaleOrder.v_delivery_method
                        record.other_terms = SaleOrder.v_terms
                elif record.document_origin[:3] == 'REM':
                    rem = self.env['remision'].search([('name', '=', record.document_origin)], limit=1)
                    if rem:
                        record.other_observations = rem.observaciones
                        record.other_delivery_method = rem.forma_entrega
                        record.other_terms = rem.condiciones
            else:
                record.other_observations = False
                record.other_delivery_method = False
                record.other_terms = False


    def action_post(self):

        # if self.metodo_pago_id.clave == 'PUE' and self.forma_pago_id.clave == '99':
        #     raise UserError(_("Forma de pago no valido"))
        # if self.metodo_pago_id.clave == 'PPD' and self.forma_pago_id.clave != '99':
        #     raise UserError(_("Forma de pago no valido"))  

        rec = super().action_post()

        self.action_invoice_open()

        return rec

    def action_invoice_open(self):

        if self.document_origin:
            if self.document_origin[:3] == 'REM':
                count = 0
                rest_cant = 0
                
                if self.remision_ids:
                    for remision in self.remision_ids:
                        for rec in self.invoice_line_ids:

                            for line in remision.remisiones_line_id:
                                if line.producto.id == rec.product_id.product_tmpl_id.id and line.description == rec.name and rec.remision_id.id == line.id_precotizador.id:  
                                    if rec.quantity > line.product_to_invoice:
                                        raise UserError(_("No se permite agregar mas productos de los que faltan por facturar."))

                                    count = abs(rec.quantity - line.product_to_invoice)
                                    line.product_to_invoice = count                                
                                    continue

                        for line_rem in remision.remisiones_line_id:
                            rest_cant += line_rem.product_to_invoice

                        if rest_cant == 0:
                            remision.update({
                                'state':'invoiced'
                            })
                        else:
                            remision.update({
                                'state':'to_invoice',
                            })    
                        count = 0
                        rest_cant = 0    

            if self.document_origin[:1] == 'S':
                so = self.env['sale.order'].search([('name','=',self.document_origin)], limit = 1)
                if len(so)>=1:
                    remission = self.env['remision'].search([('name','=',so.origin)], limit = 1)
                    if len(remission)>=1:
                        for rec in self.invoice_line_ids:

                            for line in remission.remisiones_line_id:

                                if line.producto.id == rec.product_id.product_tmpl_id.id:  
                                    if rec.quantity > line.product_to_invoice:
                                        raise UserError(_("No se permite agregar mas productos de los que faltan por facturar."))

                                    count = abs(rec.quantity - line.product_to_invoice)
                                    line.product_to_invoice = count
                                    continue                        
                        remission.update({
                            'state':'invoiced'
                        })