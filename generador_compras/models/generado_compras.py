# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import calendar
import math
import re
from odoo.exceptions import UserError, ValidationError

class generador_compras(models.Model):
    _name = 'generador.compras'
    _description = "Generador de Compras"
    _order = "fecha desc, id desc"
    _inherit = ['mail.thread']


    name = fields.Char(string='Folio',readonly=True)
    fecha = fields.Date(string='Fecha',readonly=True,default=fields.Date.today())
    user_id = fields.Many2one(comodel_name='res.users',string='Elaborado Por',default=lambda self: self.env.user,track_visibility='onchange')
    lines_ids = fields.One2many(comodel_name='generador.compras.line',inverse_name='generador_compras_id',string='Lineas de Generador')
    state = fields.Selection([('nuevo','Nuevo'),('revision','Revision'),('aplicado','Aplicado'),('cancel','Cancelado')] ,required=True, default='nuevo',track_visibility='onchange')
    periodo = fields.Char(string='Periodo',compute='_get_period',readonly=True)
    dias_laborables = fields.Float(string='Días Laborables',default=156,track_visibility='onchange')
    partner_id = fields.Many2one(comodel_name='res.partner',string='Proveedor',domain=[('supplier_rank', '>', 0)],required=True)
    dias_inventario_a = fields.Float(string='Días Inventario A',default=40.5)
    dias_inventario_b = fields.Float(string='Días Inventario B',default=40.5)
    product_category = fields.Many2many(comodel_name='product.category',string='Categoría')
    picking_type_id = fields.Many2one(comodel_name='stock.picking.type',domain=([('code','=','incoming')]),required=True,string='Almacen',track_visibility='onchange')
    subtotal_a = fields.Float(string='Subtotal A',compute='_get_subtotalab')
    subtotal_b = fields.Float(string='Subtotal B',compute='_get_subtotalab')
    total_a = fields.Float(string='Subtotal A')
    total_b = fields.Float(string='Subtotal B')
    dp_purchase_order=fields.Many2many('purchase.order','generador_compras_rel', 'generador_compras_id','purchase_order_id',string='PO')


    def cancel_sales(self):
        self.update({
            'state': 'cancel'
        })

    def update_po(self):

        purchse_order = self.env['purchase.order'].search([('origin','!=',None)])
        gen_compras = self.env['generador.compras'].search([])
        for rec in purchse_order:
            for gen in gen_compras:
                if rec.origin == gen.name:
                    gen.update({
                        'dp_purchase_order': [(4, rec.id)]
                    })

    def update_record_ab(self):
        gen_compras = self.env['generador.compras'].search([])
        for line in gen_compras:
            subtotal_a=0.00
            subtotal_b=0.00
            if line.lines_ids:
                for lines_id in line.lines_ids:
                    if lines_id.subtotal_a > 0:
                        subtotal_a+=lines_id.subtotal_a
                    if lines_id.subtotal_b > 0:
                        subtotal_b+=lines_id.subtotal_b
            line.total_a=subtotal_a
            line.total_b=subtotal_b

    def divzero(self,x,y):
        try:
            return float(x)/float(y)
        except ZeroDivisionError:
            return 0

    def _get_period(self):
        # import ipdb; ipdb.set_trace()
        date = fields.Date.today()

        for rec in self:
            rec.periodo =  date.strftime('%m')



	# def _get_period(self):
	# 	date = datetime.strptime(fields.Date.today(), '%Y-%m-%d')
	# 	for rec in self:
	# 		rec.periodo = '{:02d}'.format(date.month)

    @api.onchange('dias_laborables')
    def update_pedidos(self):
        for rec in self:
            for line in rec.lines_ids:
                line.pedido = line.sugerido_a-line.stock


    def fill_lines(self,id_header,sugeridoa,sugeridob,categorias,dias):
        end_period = fields.Date.today()
        start_period = fields.Datetime.from_string(end_period) - relativedelta(days=dias)
        start_period = start_period.date()
        # import ipdb; ipdb.set_trace()
        query="""Select ROW_NUMBER() OVER(ORDER BY prod.id DESC) AS  partida, prod.id as producto,prod.default_code as code,(
                    Select sum(case when  line.balance < 0 then line.quantity*-1
                    else line.quantity end) as qty from account_move_line as line 
                    inner join account_move as fact 
                    on fact.id = line.move_id
                    where fact.state in ('posted')  and fact.move_type='out_invoice' and fact.invoice_date between %s and %s
                    and line.product_id=prod.id
                    group by line.product_id
                    ),(select sum(line.product_qty) as bo  from stock_move as line
                    inner join stock_picking as picking 
                    on line.picking_id=picking.id
                    inner join stock_picking_type as code
                    on picking.picking_type_id=code.id
                    where picking.backorder_id is not null and picking.state='assigned' and code.code='incoming'  and line.create_date between %s and %s
                    and product_id=prod.id
                    ),(select sum(line.product_qty) as forecast  from stock_move as line
                    inner join stock_picking as picking 
                    on line.picking_id=picking.id
                    inner join stock_picking_type as code
                    on picking.picking_type_id=code.id
                    where picking.backorder_id is null and picking.state='assigned' and code.code='incoming' and code.code='incoming'  and line.create_date between %s and %s
                    and product_id=prod.id
                    )
                    from product_product as prod
                    inner join product_template as temp	
                    on temp.id=prod.product_tmpl_id
                    where temp."type"='product' and temp.categ_id in (%s)
                
    """
    
        params = (
            start_period, end_period,  # Primer BETWEEN
            start_period, end_period,  # Segundo BETWEEN
            start_period, end_period,  # Tercer BETWEEN
            tuple(categorias.ids) if hasattr(categorias, 'ids') else tuple(categorias)
        )

        self.env.cr.execute(query,params)
        line={}
        for p in self.env.cr.dictfetchall():
            bo = p['bo'] if p['bo'] else 0
            pp = p['forecast'] if p['forecast'] else 0
            line={'product_id':p['producto'],
            'total_ventas':int(p['qty']) if p['qty'] else 0 ,
            'name':p['code'],
            'generador_compras_id':id_header,
            'back_order':abs(bo)+abs(pp),
            #'purchase_planning':p['forecast'],
            'dias_inventario_a':sugeridoa,
            'dias_inventario_b':sugeridob, 
            'sequence_ref':p['partida'],
            'promedio':float(self.divzero(float(p['qty']) if p['qty'] else 0 ,dias))
            }
            self.env['generador.compras.line'].create(line)


    @api.model
    def create(self, vals):
        sugeridoa = ""
        sugeridob = ""
        if vals.get('name', 'nuevo') == 'nuevo': 
            categorias=[]
            vals['name'] = self.env['ir.sequence'].next_by_code('generador.compras') or 'Nuevo'
            sugeridoa= vals['dias_inventario_a']
            sugeridob= vals['dias_inventario_b']
            dias = vals['dias_laborables']
            for x  in  vals['product_category']:
                word_categs=str(x)
            word_categs = word_categs.replace('[','(').replace(']',')')
            ids_categ=word_categs.split('(')[-1].split(')')[0]
            ids_categ = ids_categ.replace(' ','')
            for each in ids_categ.split(','):
                categorias.append(each)
        res = super(generador_compras,self).create(vals)
        self.fill_lines(res.id,sugeridoa,sugeridob,ids_categ,dias)
        for line in  res.lines_ids:
            line.write({'pedido':line.sugerido_a-line.stock,
                        'pedido_b':line.sugerido_b-line.stock-line.back_order-line.purchase_planning})
        res.update_subtotal_ab()
        return res

	
    @api.onchange('lines_ids')
    def _get_subtotalab(self):
        for line in self:
            subtotal_a=0.00
            subtotal_b=0.00
            if line.lines_ids:
                for lines_id in line.lines_ids:
                    if lines_id.subtotal_a > 0:
                        subtotal_a+=lines_id.subtotal_a
                    if lines_id.subtotal_b > 0:
                        subtotal_b+=lines_id.subtotal_b
            line.subtotal_a=subtotal_a
            line.subtotal_b=subtotal_b


    def validate(self):
        for rec in self:
            rec.state='revision'


    def return_draft(self):
        for rec in self:
            rec.state='nuevo'



    def generar_compras(self):
        purchase_obj=self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
        # generamos orden de compra  1
        if not self.partner_id.property_purchase_currency_id.id:
            raise UserError("El proveedor {} no cuenta con una moneda de proveedor configurada".format(self.partner_id.name))
        if self.dias_inventario_a > 0:
            header= {
                'partner_id':self.partner_id.id,
                'origin':self.name,
                'state':'draft',
                'picking_type_id':self.picking_type_id.id,
                'currency_id': self.partner_id.property_purchase_currency_id.id
                }
            # lines = []
            purchase_order = purchase_obj.create(header)
            for line in self.lines_ids:
            # for line in rec.env['mfg.material.extra.line'].search([('default_supplier','=',p['default_supplier'])]):
                detail= {
                    'date_planned':fields.Date.today(),
                    'name': line.name,
                    'product_id':line.product_id.id,
                    'product_qty':line.pedido,
                    'product_uom':line.product_id.uom_id.id,
                    'price_unit':line.product_id.standard_price,
                    'taxes_id':[(6,0,line.product_id.supplier_taxes_id.ids)],
                    'order_id':purchase_order.id,
                    }
                if line.pedido > 0:
                    Newrow = purchase_line_obj.create(detail)
                else:
                    continue
                # lines.append(Newrow)
        if self.dias_inventario_b > 0 :
            # generamos orden de compra  2 proyectado
            header= {
                'partner_id':self.partner_id.id,
                'origin':self.name,
                'state':'draft',
                'picking_type_id':self.picking_type_id.id,
                'currency_id': self.partner_id.property_purchase_currency_id.id
                }
            # lines = []
            purchase_order = purchase_obj.create(header)
            for line in self.lines_ids:
            # for line in rec.env['mfg.material.extra.line'].search([('default_supplier','=',p['default_supplier'])]):
                detail= {
                    'date_planned':fields.Date.today(),
                    'name': line.name,
                    'product_id':line.product_id.id,
                    'product_qty':line.pedido_b,
                    'product_uom':line.product_id.uom_id.id,
                    'price_unit':line.product_id.standard_price,
                    'taxes_id':[(6,0,line.product_id.supplier_taxes_id.ids)],
                    'order_id':purchase_order.id,
                    }
                if line.pedido_b > 0 :
                    Newrow = purchase_line_obj.create(detail)
                else:
                    continue
        
                # lines.append(Newrow)
        self.state='aplicado'
        self.update({
            'state': 'aplicado',
            'dp_purchase_order': [(4, order_id.id, None) for order_id in purchase_order]
        })

    def write(self, vals):
        res = super(generador_compras, self).write(vals)
        if vals.get('lines_ids'):
            if any( line[2] != False for line in vals.get('lines_ids')):
                self.update_subtotal_ab()
            
        return res

    def update_subtotal_ab(self):
        for line in self:
            subtotal_a=0.00
            subtotal_b=0.00
            if line.lines_ids:
                for lines_id in line.lines_ids:
                    if lines_id.subtotal_a > 0:
                        subtotal_a+=lines_id.subtotal_a
                    if lines_id.subtotal_b > 0:
                        subtotal_b+=lines_id.subtotal_b
            line.total_a=subtotal_a
            line.total_b=subtotal_b

class generador_compras_line(models.Model):
    _name = 'generador.compras.line'
    _order= 'sequence_ref asc'

    product_id = fields.Many2one(comodel_name='product.product',string='Articulo',readonly=True , index=True)
    name = fields.Char(string='Clave',index=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    total_ventas = fields.Integer(string='Ventas Total',readonly=True)
    promedio = fields.Float(string='Promedio',readonly=True)
    sugerido_a = fields.Integer(string='Sugerido A',compute='_get_sugerido')
    sugerido_b = fields.Integer(string='Sugerido B',compute='_get_sugerido')
    pedido = fields.Integer(string='Pedido A')
    pedido_b = fields.Integer(string='Pedido B')
    back_order = fields.Integer(string='BO',readonly=True)
    purchase_planning= fields.Integer(string='PR',readonly=True)
    costo = fields.Float(string='C/U',related='product_id.standard_price',readonly=True)
    stock = fields.Integer(string='Existencia',compute='_get_stock_avalaible')
    # default_supplier = fields.Many2one(comodel_name='res.partner',string='Proveedor',compute='_compute_get_default_supplier')
    dias_inventario_a = fields.Float(string='Días Inventario A',default=40.5)
    dias_inventario_b = fields.Float(string='Días Inventario B',default=40.5)
    back_order_qyt = fields.Float(string='Back Order')
    subtotal_a = fields.Float(string='cto A' ,compute='_get_subtotal')
    subtotal_b = fields.Float(string='cto B' ,compute='_get_subtotal')
    generador_compras_id = fields.Many2one(comodel_name='generador.compras')
    categoria_linea = fields.Many2one(comodel_name='product.category',string='Linea',related='product_id.product_tmpl_id.categ_id',readonly=True)
    sequence_ref = fields.Integer('No.',index=True)

    # 
    # def _prepare_order_line_procurement(self, group_id=False):
    # 	self.ensure_one()
    # 	vals = super(generador_compras_line, self)._prepare_order_line_procurement(group_id=group_id)
    # 	vals.update({'sequence_ref':self.sequence_ref})
    # 	return vals
    
    def unlink(self):
        # Add code here
        print ("entro al borrado")
        no = 0
        for l in self.generador_compras_id.lines_ids:
            no += 1
            l.write({'sequence_ref':no})
        return super(generador_compras_line, self).unlink()


    @api.onchange('pedido','pedido_b')
    def _get_subtotal(self):
        for rec in self:
            rec.subtotal_a = rec.costo * rec.pedido
            rec.subtotal_b = rec.costo * rec.pedido_b


    def divzero(self,x,y):
        try:
            return x/y
        except ZeroDivisionError:
            return 0

    @api.onchange('dias_inventario_a','dias_inventario_b')
    def _get_sugerido(self):
        for rec in self:
            rec.sugerido_a = math.ceil(rec.promedio*rec.dias_inventario_a)
            rec.sugerido_b = math.ceil(rec.promedio*(rec.dias_inventario_a+rec.dias_inventario_b))

    def _get_stock_avalaible(self):
        for rec in self:
            rec.stock = rec.product_id.free_qty



class ExtraFieldsFacturasProvedor(models.Model):
    _inherit ='account.move'


    amount_mxn = fields.Float(string='Total MXN',compute='_get_amount_mxn',store = True)
    diary_value = fields.Float(string='TC',compute='_get_amount_mxn',digits=(9,4))

    # Falta migrar
    @api.depends('amount_total')
    def _get_amount_mxn(self):
        pass
        # for rec in self:
        # 	if rec.move_id.line_ids:
        # 		if rec.move_id.line_ids[0].amount_currency != 0.0:
        # 			if rec.move_id.line_ids[0].credit != 0.0:
        # 				rec.diary_value = (rec.move_id.line_ids[0].credit/(rec.move_id.line_ids[0].amount_currency*-1))
        # 	if rec.currency_id.name != 'MXN':
        # 		rec.amount_mxn = rec.amount_total * rec.diary_value
        # 	else:
        # 		rec.amount_mxn= rec.amount_total


    def get_account_pay(self):
        if self.move_type == 'in_invoice':
            self.write({
                'account_id': self.partner_id.property_account_payable_id.id
            })
            self.env.cr.commit()


    def _get_amount_mxn_update(self):
        sup_invoices = self.env['account.move'].search([('move_type','=','in_invoice')])
        for rec in sup_invoices:
            if rec.line_ids:
                if rec.line_ids[0].amount_currency != 0.0:
                    if rec.line_ids[0].credit != 0.0:
                        rec.diary_value = (rec.line_ids[0].credit/(rec.line_ids[0].amount_currency*-1))
            if rec.currency_id.name != 'MXN':
                rec.amount_mxn = rec.amount_total * rec.diary_value
            else:
                rec.amount_mxn= rec.amount_total

class invoicecrearnuevo(models.Model):
	_inherit = "account.move"

	destination_invoice =fields.Char(string = 'Destino', track_visibility='onchange')


	def get_filds_cfdi(self):
		if self.move_type == 'out_invoice':
			client = self.env['res.partner'].search([('id','=',self.partner_id.id)])

			self.write({
				'forma_pago_id': client.forma_pago_id.id,
				'metodo_pago_id': client.metodo_pago_id.id,
				'uso_cfdi_id': client.uso_cfdi_id.id
			})
			self.env.cr.commit()

