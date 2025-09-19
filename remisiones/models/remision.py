# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from datetime import date, datetime, timedelta
from odoo import api, fields, models, _,SUPERUSER_ID
from odoo import exceptions
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class remisiones(models.Model):
    _name = 'remision'
    _inherit = ['mail.thread']

    
    name=fields.Char(readonly=True, index=True, tracking=True, string="Remisión")
    partner_id=fields.Many2one(comodel_name='res.partner',string='Cliente',tracking=True)
    remisiones_line_id=fields.One2many(comodel_name='remision_line',inverse_name='id_precotizador',tracking=True)
    pickin_id=fields.One2many(comodel_name='stock.picking',inverse_name='id_remision')
    id_sale=fields.Many2one(comodel_name='sale.order', string="Venta")
    user_id=fields.Many2one(string="Usuario", comodel_name='res.users', compute='_get_default_user',tracking=True)
    default_warehouse=fields.Many2one(string="Almacen por defecto", comodel_name='stock.warehouse', compute='_get_default_warehouse')
    clave_de_cliente=fields.Char(string= 'Clave del cliente', compute = '_get_client_id')
    pedido_cliente=fields.Char(string= 'Pedido del cliente',tracking=True)
    contacto=fields.Char(string= 'Contacto',tracking=True)
    forma_entrega=fields.Char(string= 'Forma de entrega',tracking=True)
    condiciones=fields.Char(string= 'Condiciones',tracking=True)
    gia=fields.Char(string= 'Guia',tracking=True)
    observaciones=fields.Text(string="Observaciones",tracking=True)
    fecha_documento=fields.Date(string='Fecha', default=fields.Date.today(), readonly=True)
    fecha_vencimiento=fields.Date(string="Fecha de vencimiento",tracking=True)
    importe=fields.Float(string="Importe", compute='_get_importe')
    subtotal=fields.Float(string="Subtotal", compute='_get_subtotal')
    descuento_total=fields.Float(string="")
    total=fields.Float(string="Total", compute='_get_total')
    total_tree=fields.Float(string="Total", compute='_get_importe_tree')
    iva=fields.Float(string="IVA", compute="_get_iva")
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    stock_picking_id = fields.Many2one(comodel_name='stock.picking')
    count_picking_rem = fields.Integer(compute='action_view_delivery',string=' ')
    menssage=fields.Char(compute='_compute_menssage')
    state=fields.Selection([('draft','Borrador'),
        ('proceso', 'En proceso'),
        ('send','Remisión enviada'),
        ('remission', 'En remisión'),
        ('done', 'En presupuesto'),
        ('to_invoice','Por facturar'),
        ('closed','Cerrada'),
        ('invoiced','Facturado'),
        ('cancelled', 'Cancelado')],string="Estado",readonly=True, copy=False, index=True, default='draft',tracking=True)

    message_residence=fields.Char()
    message_logistic=fields.Char()
    message_sales=fields.Char()
    message_client=fields.Char()
    message_remission=fields.Char()
    sales_flag = fields.Boolean()
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')
    invoice_count = fields.Integer(string='Facturas', compute='_compute_invoice_ids')
    invoice_id =fields.Many2one(comodel_name='account.move',string='Factura')
    invoice_ids = fields.Many2many(comodel_name='account.move', string= 'Facturas')
    flag_remision = fields.Boolean(string = '', compute='_compute_flag')
    product_id = fields.Many2one('product.template', related='remisiones_line_id.producto', string='Producto')
    email_message = fields.Char(string='Remision enviada', readonly=True)
    email_send = fields.Boolean(string='',store=True, compute = '_compute_email_rem')
    motive = fields.Selection([
        ('material_view', 'Material a vistas'),
        ('material_wrong', 'Material reposición mal entregado'),
        ('material_warranty', 'Material por garantía'),
        ('material_expo', 'Material para exposiciones'),
        ('client_not_credit', 'Cliente sin crédito'),
        ('client_not_register', 'Cliente sin registro')
    ], string='Motivo',tracking=True)
    motive_flag = fields.Boolean(string='')
    package = fields.Char(string = 'Paqueteria',tracking=True)
    destiny = fields.Char(string = 'Destino',tracking=True)
    comercial_id = fields.Many2one(comodel_name='res.users', string='Comercial', store=True)

    flag_other_info = fields.Boolean(compute='_compute_other_info')


    def _compute_other_info(self):
        for record in self:
            if record.invoice_ids and any(inv.state in ['draft','posted','cancel'] for inv in record.invoice_ids):
                record.flag_other_info = True
            else:
                record.flag_other_info = False

    def get_comercial(self):
        if self.partner_id.vat == 'XAXX010101000':
            return ""
        else:
            
            return self.partner_id.user_id.name


    @api.depends('state')
    def _compute_email_rem(self):
        if self.state == 'draft' and len(self.pickin_id) > 0:
            query = """UPDATE remisionesgovar_remisiones SET email_send = True WHERE id = {}""".format(self.id)
            self.env.cr.execute(query)

    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        warning = {}
        title = False
        message = False
        partner = self.partner_id

        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.sale_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.sale_warn != 'block' and partner.parent_id and partner.parent_id.sale_warn == 'block':
                partner = partner.parent_id
            if partner.sale_warn == 'block':
                title = ("CLIENTE BLOQUEADO")
            if partner.sale_warn == 'warning':
                title = ("AVISO")

            message = partner.sale_warn_msg
            warning = {
                    'title': title,
                    'message': message,
            }
            if partner.sale_warn == 'block':
                return {'warning': warning}

        if warning:
            return {'warning': warning}


    def directions_line(self):
        return self.env.user.company_id.directions_line_id

    def close_remision(self):
        self.update({
            'state': 'closed'
        })

    def _get_client_id(self):
        self.clave_de_cliente = self.partner_id.id            

    #FIXME REVISAR codigo
    @api.depends('remisiones_line_id', 'remisiones_line_id.product_to_invoice', 'state')
    def _compute_flag(self):
        for rec in self:
            quantity = 0
            for line in rec.remisiones_line_id:
                quantity += line.product_to_invoice
            
            if quantity > 0 and rec.state in ['remission', 'to_invoice']:
                rec.flag_remision = True
            else:
                rec.flag_remision = False

    @api.depends('pickin_id')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.pickin_id)

    @api.depends('invoice_ids')
    def _compute_invoice_ids(self):
        for order in self:
            order.invoice_count = len(order.invoice_ids)


    def validate_remision(self):
        flag_pickin = True

        for rec in self:
            if rec.state not in ['remission','to_invoice']:
                raise exceptions.ValidationError('Una de las facturas no se encuentra en estado En remisión o Por facturar')

            if rec.pickin_id:
                for picking in rec.pickin_id:
                    if picking.state not in ['done','cancel']: 
                        flag_pickin = False
            if flag_pickin == False:
                raise exceptions.ValidationError('No se puede crear la factura, hasta entregar la mercancía')
            flag_pickin = True
     
            if any(inv.state == 'draft' for inv in rec.invoice_ids):
                raise UserError(_("Existe una factura en borrador"))

        if any(rem.partner_id != self[0].partner_id for rem in self):
            raise UserError(_("Las remisiones tiene que pertenecer al mismo cliente"))

    def total_remision(self):
        
        origin = ""
        list_origin = []

        self.validate_remision()
        view_id = self.env.ref('account.view_move_form').id

        for rec in self:
            list_origin.append(rec.name)
        
        origin = ", ".join(list_origin)

        invoice = self.env['account.move'].create({
            #'name': order.client_order_ref or order.name,
                'document_origin': origin,
                'move_type': 'out_invoice',
                'partner_id': self[0].partner_id.id,
                'journal_id': self[0].env['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', self[0].env.user.company_id.id)], limit=1).id,
                'currency_id': self[0].env.user.company_id.currency_id.id,
                'invoice_payment_term_id': self[0].partner_id.property_payment_term_id.id,
                'team_id': self[0].env.user.sale_team_id.id if hasattr(self[0].env.user, 'sale_team_id') else False,
                'user_id': self[0].env.user.id,
                'company_id': self[0].env.user.company_id.id,
                'remision_ids': [(6, 0, self.ids)],
                'other_delivery_method': self[0].forma_entrega,
                'other_terms': self[0].condiciones,
                'package': self[0].package,
                'destination_invoice': self[0].destiny,
                # 'comment': order.note,
        })
        # Crear líneas de factura usando el método estándar de Odoo
        invoice_lines = []
        for remision in self:
            for rec in remision.remisiones_line_id:
                producto = self.env['product.product'].search([('product_tmpl_id', '=', rec.producto.id)])
                if rec.product_to_invoice > 0:
                    line_invoice = {
                        'move_id': invoice.id,
                        'product_id':producto.id,
                        'quantity':rec.product_to_invoice,
                        'price_unit':rec.valor_unitario,
                        'origin': remision.name,
                        'product_uom_id': producto.uom_id.id,
                        'account_id': producto.property_account_income_id.id or producto.categ_id.property_account_income_categ_id.id,
                        'partner_id': self[0].partner_id.id,
                        'company_id': self[0].env.user.company_id.id,
                        'name': rec.description or "[{}] {}".format(producto.default_code, producto.product_tmpl_id.name),
                        'remision_id': remision.id                        
                    }
                    if rec.tax_id:
                        line_invoice['tax_ids'] = [(6,0,rec.tax_id.ids)]
                    invoice_lines.append((0, 0, line_invoice))

        # Actualizar la factura con las líneas
        invoice.write({'invoice_line_ids': invoice_lines})
        
        # Calcular impuestos y balancear el asiento
        invoice._compute_amount()
        invoice._recompute_dynamic_lines(recompute_all_taxes=True)
        for remision in self:
            remision.update({
                'invoice_id':invoice,
                'invoice_ids': [(4, invoice.id)],
                'state': 'to_invoice',
                'message_remission': 'Remision total'
            })
        
        return {
            'name': _('Account Invoice'),
            'view_mode': 'form',
            'res_model': 'account.move',
			'res_id': invoice.id,
            'type': 'ir.actions.act_window',
			'views': [[view_id,'form']],

        }

    
    def parcial_remision(self):
        for line in self:
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
            for x in picking.move_line_ids:
                x.qty_done=x.product_qty
            picking.button_validate()
            sale = self.env['sale.order'].create({
                'partner_id':line.partner_id.id,
                'payment_term_id':line.partner_id.property_payment_term_id.id,
                'warehouse_id':line.default_warehouse.id,
                # 'user_id':line.partner_id.user_id.id,
                'picking_policy':'direct',
                'client_order_ref':line.clave_de_cliente,
                # 'v_observations':line.observaciones,
                # 'v_delivery_method':line.forma_entrega,
                # 'v_terms':line.condiciones,
                'origin':line.name,
            })
            line.write({'id_sale':sale.id})
            for rec in line.remisiones_line_id:
                producto = self.env['product.product'].search([('product_tmpl_id', '=', rec.producto.id)])
                self.env['sale.order.line'].create({
                    'product_id':producto.id,
                    'product_uom_qty':rec.cantidad,
                    'price_unit':rec.valor_unitario,
                    'tax_id':[(6,0,[rec.tax_id.id])],
                    # 'price_list':rec.price_list,  # Campo no disponible en Odoo 15
                    'order_id':sale.id,
                    'name':"["+producto.default_code+"] "+producto.product_tmpl_id.name,
                    })
            line.state='done'

        self.update({
            'message_remission': 'Remision parcial'
        })
    
    def send_email_remission(self):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('ventas_govar', 'email_template_remission')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'remision',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "ventas_govar.email_template_remission",
            'default_partner_ids': self.partner_id.ids,
        })

        return {
            'type': 'ir.actions.act_window',
        
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    
    def action_submit(self):        
        body =_("Expense Advance Submitted")
        subject = _("Expense Advance")
        self.sudo().message_post(body=body,subject=subject, message_type="notification", subtype="mail.mt_comment", author_id=SUPERUSER_ID)
 
    
    def action_view_delivery(self):

        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('pickin_id')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        return action

    
    def action_view_invoice(self):


        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    
    def print_pdf(self):

        self.ensure_one()
        return self.env['report'].get_action(self, 'ventas_govar.report_remisiones')

    def get_name_remision(self):

        if self.state in ['draft','proceso','cancelled','send','closed']:
            return "Remisión"
        elif self.state in ['remission','done','to_invoice','invoiced']:
            return "Remisión validada"

    
    @api.onchange('descuento_total')
    def _onchange_listprice(self):
        for line in self:
            if line.descuento_total < 0:
                line.descuento_total*=-1
            

    @api.model
    def create(self, vals):
        # import ipdb; ipdb.set_trace()  # Debug removido
        sucursal = self.env.user.property_warehouse_id

        if not sucursal:
            raise exceptions.ValidationError('No se puede crear una remision sin tener un almacen designado')

        now=fields.Datetime.now()
        fecha = fields.Datetime.from_string(now) + relativedelta(days=7)
        seq = self.env['ir.sequence'].next_by_code('seq_remisiones') or '/'
        code = seq
        if sucursal.name == 'MATRIZ':
            code = "REMM{}".format(seq[3:])
        if sucursal.name == 'PERIFERICO':
            code = "REMP{}".format(seq[3:])
        if sucursal.name == 'EJERCITO':
            code = "REME{}".format(seq[3:])
        vals['fecha_vencimiento'] = fecha
        vals['name'] = code

        res = super(remisiones, self).create(vals)

        res.partner_id.update({
            'rem_ids': [(4, res.id)]
        })

        return res

    
    def _get_default_user(self):
        for line in self:
            line.user_id=line._context.get('uid')

    
    def _get_default_warehouse(self):
        for line in self:
            line.default_warehouse=line.create_uid.property_warehouse_id

    
    @api.onchange("remisiones_line_id")
    def _get_importe(self):
        total=0.00

        for line in self:
            for lin in line.remisiones_line_id:
                total+=lin.valor_unitario * lin.cantidad
        if line.remisiones_line_id:
            line.importe=total

    
    @api.depends('remisiones_line_id')
    def _get_iva(self):
        """Calcula el IVA usando"""
        for record in self:
            total_tax = 0.0
            
            for line in record.remisiones_line_id:
                if line.tax_id and line.valor_unitario and line.cantidad:
                    # Usar el mismo método que sale.order.line._compute_amount()
                    price = line.valor_unitario
                    taxes = line.tax_id.compute_all(
                        price, 
                        record.currency_id or self.env.company.currency_id, 
                        line.cantidad, 
                        product=line.producto, 
                        partner=record.partner_id
                    )
                    # Sumar todos los impuestos de esta línea
                    line_tax = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    total_tax += line_tax
            
            record.iva = total_tax



    @api.depends('remisiones_line_id', 'remisiones_line_id.importe', 'iva')
    def _get_importe_tree(self):
        """Calcula el total para mostrar en vista tree (incluye IVA)"""
        for remision in self:
            subtotal = sum(line.importe for line in remision.remisiones_line_id)
            remision.total_tree = subtotal + remision.iva

    
    @api.onchange("importe","descuento_total")
    def _get_subtotal(self):
        for remision in self:
            remision.subtotal=remision.importe-remision.descuento_total

    
    @api.onchange("subtotal","iva","descuento_total","remisiones_line_id")
    def _get_total(self):
        for line in self:
            line.total=line.subtotal+line.iva

    def validate_client(self):
        if not self.env.user.has_group('ventas_govar.confirm_rem'):
            partner_name = self.partner_id.name.replace(" ","")
            if partner_name.upper() == 'PUBLICOENGENERAL':
                raise UserError("Confirmar pago con credito y cobranza")

    
    @api.onchange('partner_id')
    def validate_clint_pg(self):

        if self.partner_id and self.motive_flag == True:
            partner_name = self.partner_id.name.replace(" ","")
            if partner_name.upper() == 'PUBLICOENGENERAL':
                raise UserError("Confirmar pago con credito y cobranza")

    @api.onchange('partner_id')
    def _onchange_partner_motive(self):
        for rec in self:
            rec.motive_flag = self.env.user.company_id.message_rem_mot

    
    def crear_pickin(self):
        warning = {}
        title = False
        message = False
        partner = self.partner_id		


        if not self.user_has_groups('remisiones.price_rem_so') and self.partner_id.less_price == False and self.partner_id.company_id.list_validate == True:
            self.validate_price_rem_3()
        
        if self.motive_flag == True:
            self.validate_client()

        if partner.sale_warn != 'no-message':
            title = f"Advertencia{partner.name}"
            message = partner.sale_warn_msg
            warning = {
                    'title': title,
                    'message': message,
            }
            if partner.sale_warn == 'block':
                raise UserError(_(f'CLIENTE BLOQUEADO \n {message} '))	
        warehouse_obj = self.env['stock.warehouse']

        for rec in self.remisiones_line_id:
            product = self.env['product.product'].search([('product_tmpl_id', '=', rec.producto.id)])
            if product:
                if product.product_tmpl_id.type == 'product':
                    warehouse_list = warehouse_obj.search([('id','=',self.env.user.property_warehouse_id.id)])
                    available_qty = product.with_context({'warehouse' : warehouse_list.id}).free_qty

                    if available_qty <= 0:
                        raise exceptions.ValidationError("No hay suficiente material del producto ingresado \n {}".format(product.name))   

        for line in self:
            location= self.env['stock.location'].search([('name', '=', 'REMISION'),('usage','=','customer',)])
            outgoing = self.env['stock.picking.type'].search([('code', '=', 'outgoing'),('warehouse_id','=',line.default_warehouse.id,)])
            picking = self.env['stock.picking'].create({
                'partner_id':line.partner_id.id,
                'origin':line.name,
                'picking_type_id':outgoing[0].id,
                'location_id':line.default_warehouse.lot_stock_id.id,
                'location_dest_id':location.id,
                'id_remision':line.id,
                'is_remision': True,          
                })

            line.stock_picking_id=picking.id
            for rec in line.remisiones_line_id:
                producto = self.env['product.product'].search([('product_tmpl_id', '=', rec.producto.id)])
                if producto.type == 'product':
                    self.env['stock.move'].create({
                        'product_id':producto.id,
                        'product_uom_qty':rec.cantidad,
                        'product_uom':rec.unidad_medida.id,
                        'picking_id':picking.id,
                        'location_id':line.default_warehouse.lot_stock_id.id,
                        'name':"["+producto.default_code+"] "+producto.product_tmpl_id.name,
                        'location_dest_id':location.id,
                        })
                
            picking.action_confirm()
            picking.action_assign()
            line.state='proceso'


    def validate_price_rem_3(self):

        for rec in self.remisiones_line_id:
            if not rec.producto.id == False:
                pass
                # price_list_3 = self.env['fixed.prices'].sudo().search([('list_num','=',3),('product_id','=',rec.producto.id)]).price  # Modelo personalizado no disponible en Odoo 15
                # if rec.valor_unitario < round((price_list_3 ),2 ) and rec.valor_unitario > 0.00 and price_list_3 > 0.00:
                #     raise UserError(u"El precio unitario del producto {} no puede ser menor al precio de {}".format(rec.producto.name,round((price_list_3),2 )))  # Validación deshabilitada por modelo personalizado no disponible                 
                # else:
                #     rec.importe=rec.cantidad*rec.valor_unitario


    
    def _compute_menssage(self):
        
        for line in self:
            menssage=0
            if not line.pickin_id:
                menssage=1
            for pick in line.pickin_id:
                if pick.picking_type_code=='outgoing':
                    if not pick.move_line_ids:
                        menssage=1
                    for producto in pick.move_line_ids:
                        if producto.product_qty-producto.qty_done !=0:
                            menssage=1
                        if pick.state !='done':
                            menssage=1
            if menssage==0:
                line.menssage='Producto surtido'
                if line.state in ("proceso"):
                    line.write({'state':'remission'})
                    
            else:
                line.menssage=''
                

    
    def crear_pedido(self):
        for line in self:
            location= self.env['stock.location'].search([('name', '=', 'REMISION'),('usage','=','customer',)])
            outgoing = self.env['stock.picking.type'].search([('code', '=', 'incoming'),('warehouse_id','=',line.default_warehouse.id,)])
            picking = self.env['stock.picking'].create({
                'partner_id':line.partner_id.id,
                'origin':line.name,
                'picking_type_id':outgoing[0].id,
                'location_id':location.id,
                'location_dest_id':line.default_warehouse.lot_stock_id.id,
                'id_remision':line.id,
                'is_remision': True
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
            for x in picking.move_line_ids:
                x.qty_done=x.product_qty
            picking.button_validate()
            iva=self.env['account.tax'].search([('type_tax_use','=','sale'),('name','=','IVA(16%) VENTAS',)])            
            sale = self.env['sale.order'].create({
                'partner_id':line.partner_id.id,
                'payment_term_id':line.partner_id.property_payment_term_id.id,
                'warehouse_id':line.default_warehouse.id,
                'user_id':line.partner_id.user_id.id,
                # 'picking_policy':'direct',
                # 'client_order_ref':line.clave_de_cliente,
                # 'note':line.observaciones + ' - ' + line.condiciones if line.observaciones or line.condiciones else '',
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
                    # 'price_list':rec.price_list,  # Campo no disponible en Odoo 15
                    'order_id':sale.id,
                    'name':"["+producto.default_code+"] "+producto.product_tmpl_id.name,
                    })
            line.state='done'
        self.update({
                'message_remission': 'Remision parcial'
            })

    
    def cancel_referral(self):
        flag_dev = True
        if self.state == 'draft': 
            self.update({
                'state': 'cancelled',
                'message_remission': 'Remision canelada'
            })
            return True
        if self.pickin_id:
            for rec in self.pickin_id:
                if rec.state != 'cancel':
                    flag_dev = False
            for rec in self.pickin_id:
                if rec.picking_type_id.code == 'incoming' and rec.state == 'done':
                    flag_dev = True
        if flag_dev == True:
            self.update({
                'state': 'cancelled',
                'message_remission': 'Remision cancelada'
            })
        else:
            raise exceptions.ValidationError('No se puede cancelar la remisión hasta devolver la mercancia')




class remisiones_line(models.Model):
    _name = 'remision_line'

    # FIXME Pendiente a precio de lista
    # @api.depends('producto')
    # def _compute_price_list(self):
    #     return self.id_precotizador.partner_id.list_num

    producto=fields.Many2one(string="Producto",comodel_name='product.template')
    tax_id = fields.Many2many(comodel_name='account.tax',string='Impuestos')
    unidad_medida=fields.Many2one(string="Unidad de medida",comodel_name='uom.uom',related='producto.uom_id')
    cantidad=fields.Float(string="Cantidad", default = 1)
    valor_unitario=fields.Float(string="Precio unitario")
    importe=fields.Float(string="Importe", compute='_compute_importe', store=True)
    id_precotizador=fields.Many2one(inverse_name='remisiones_line_id',comodel_name="remision", string="remision",invisible=True)
    # price_list = fields.Integer(string="Lista",default = _compute_price_list, store= True)
    # avaible_stock = fields.Char(string='Stock', compute = '_get_stock_popup_rem')
    inernt_category = fields.Char(related='producto.categ_id.name',string="Categoria interna")
    product_to_invoice = fields.Float(string = 'Cantidad facturada')
    description = fields.Char(string = 'Descripcion')
    # category_layout =fields.Many2one(comodel_name='sale.layout_category', string="Sección")
    delivery_time = fields.Integer(string="Tiempo inicial entrega")
    quantity_delivery = fields.Integer(string="Cantidad Entregada")

    
                     
    
    @api.onchange('cantidad', 'valor_unitario')
    def onchange_importe(self):
        """Calcula el importe automáticamente"""
        for line in self:
            print("****************")
            print("Entrooo")
            print(line.cantidad)
            print(line.valor_unitario)
            print(line.cantidad * line.valor_unitario)
            print("****************")
            line.importe = line.cantidad * line.valor_unitario

    @api.depends('remisiones_line_id.importe')
    def _get_importe(self):
        """Calcula el importe total sumando los importes de las líneas"""
        for remision in self:
            remision.importe = sum(line.importe for line in remision.remisiones_line_id)




    @api.depends('remisiones_line_id', 'remisiones_line_id.importe')
    def _get_importe_tree(self):
        """Calcula el total para mostrar en vista tree"""
        for remision in self:
            remision.total_tree = sum(line.importe for line in remision.remisiones_line_id)


    # @api.onchange('producto')
    # def _onchange_listprice(self):
    #     for line in self:
            # line.price_list = line.id_precotizador.partner_id.list_num or 1  # Campo no disponible en Odoo 15
            # if not line.producto.id == False:
            #     pass
                # line.valor_unitario = self.env['fixed.prices'].sudo().search([('list_num','=',line.price_list),('product_id','=',line.producto.id)]).price  # Modelo personalizado no disponible en Odoo 15
                # line.importe=line.cantidad*line.valor_unitario
                # line.description = "[{}]{}".format(line.producto.default_code,line.producto.name.encode('utf-8'))

    @api.onchange('producto')
    def _onchange_producto(self):
        """Actualiza automáticamente precio, impuestos y descripción al seleccionar un producto"""
        for line in self:
            if line.producto:
                # Actualizar precio unitario
                line.valor_unitario = line.producto.list_price
                
                # Obtener impuestos del producto
                if line.producto.taxes_id:
                    # Filtrar impuestos de venta para la empresa actual
                    taxes = line.producto.taxes_id.filtered(lambda t: t.type_tax_use == 'sale' and t.company_id == self.env.company)
                    if taxes:
                        line.tax_id = [(6, 0, taxes.ids)]
                
                # Actualizar descripción
                line.description = f"[{line.producto.default_code or ''}] {line.producto.name}"
                
                # Actualizar importe
                line.importe = line.cantidad * line.valor_unitario
                
                # Actualizar product_to_invoice
                line.product_to_invoice = line.cantidad



    # @api.onchange('producto')
    # def _get_stock_popup_rem(self):
    #     for rec in self:
    #         stock_string=""
    #         warehouse_obj = self.env['stock.warehouse']
    #         product = self.env['product.product'].search([('product_tmpl_id','=',rec.producto.id)])
    #         warehouse_list = warehouse_obj.search([('view_on_sale','=',True)])
    #         for warehouse in  warehouse_list:
    #             available_qty = product.with_context({'warehouse' : warehouse.id}).free_qty
    #             stock_string = stock_string + warehouse.code + " -> " + str(available_qty) + ("\n")
    #         rec.avaible_stock=stock_string



    @api.model
    def create(self, vals):

        vals['product_to_invoice'] = vals['cantidad']
        vals['importe'] = vals['cantidad'] * vals['valor_unitario']
        rec = super(remisiones_line, self).create(vals)

        rec.producto.update({
            'rem_ids': [(4, rec.id)]
        })
        return rec


    @api.model
    def write(self, vals):
        if vals.get('cantidad'):
            vals['product_to_invoice']= vals.get('cantidad')
            vals['importe'] = vals.get('cantidad') * self.valor_unitario
            
        if vals.get('valor_unitario'):
            vals['valor_unitario'] = vals.get('valor_unitario')
            vals['importe'] = vals.get('valor_unitario') * self.cantidad

        if vals.get('cantidad') and vals.get('valor_unitario'):
            vals['product_to_invoice'] = vals.get('cantidad')      
            vals['importe'] = vals.get('valor_unitario') * vals.get('cantidad')

        return super(remisiones_line, self).write(vals)


