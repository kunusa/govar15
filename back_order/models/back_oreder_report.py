from odoo.exceptions import UserError
from odoo import fields, models, api
from datetime import datetime, date, timedelta
from pytz import timezone
from io import BytesIO
import logging
import base64

_logger = logging.getLogger(__name__)
try:
	import xlsxwriter
except ImportError:
	_logger.warning("Cannot import xlsxwriter")
	xlsxwriter = False


# from xlsxwriter.utility import xl_rowcol_to_cell	

class ProductReportBackOrder(models.Model):
    _name = "product.report.back"
    _rec_name = 'code_report'

    code_report = fields.Char(string='Folio',readonly=True, index=True, tracking=True,)
    initial_date = fields.Date(string = 'Desde')
    final_date = fields.Date(string = 'Hasta')
    compare_initial_date = fields.Date(string = 'Desde')
    compare_final_date = fields.Date(string = 'Hasta')
    product_category_id = fields.Many2many('product.category', 'product_report_stock_categ_rel', 'product_report_stock_id',
        'categ_id', 'Categorias')
    product_category = fields.Boolean(string='Por categoria')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    product_ids = fields.Many2many('product.product', 'product_report_back_stock_rel', 'product_report_back_stock_id',
        'product_id', 'Productos')
    partner_id = fields.Many2many('res.partner', 'supplier_report_back_rel', 'supplier_report_back_id',
        'partner_id', 'Proveedor', domain="[('supplier_rank', '>', 0)]")
    lines_ids = fields.One2many(comodel_name='back.order.line',inverse_name='back_order_id',string='Lineas de productos')
    all_supplier = fields.Boolean(string='Todos los proveedores')
    all_products = fields.Boolean(string ='Todos los productos')

    @api.model
    def create(self, vals):

        vals['code_report'] = self.env['ir.sequence'].next_by_code('product.report.back') or 'Nuevo'
        res = super(ProductReportBackOrder,self).create(vals)

        #Realiza busqueda solo por proveedores
        if res.partner_id and not res.product_ids:
            result = self.get_info_purchase(vals)
            self.get_result_supplier(res,result)
        elif res.all_supplier:
            result = self.get_info_purchase(vals)
            self.get_result_supplier(res,result)
        #Realiza busqueda solo por productos
        if res.product_ids  and not res.partner_id:
            result_product = self.get_info_by_product(vals)       
            self.get_result_product(res,result_product)
        elif res.all_products:
            result_product = self.get_info_by_product(vals)       
            self.get_result_product(res,result_product)         
        #Realiza busqueda proveedores y productos
        if res.product_ids  and res.partner_id:
            result = self.get_info_product_supplier(vals)
            self.get_result_product(res,result)
        return res


    def get_result_product(self,res,result_product):
        move_flag = False
        line = {}
        
        for rec in result_product:
            for move in rec.move_ids:
                if move.state == 'assigned':
                    move_flag = True            
            if move_flag == True:
                line={                        
                    'supplier':rec.partner_id.name,
                    'quatation_id':rec.order_id.id,
                    'date_po':rec.date_order,
                    'code':rec.product_id.default_code,
                    'product':rec.product_id.name,
                    'category': rec.product_id.product_tmpl_id.categ_id.name,
                    'quanity':abs(rec.product_qty - rec.qty_received),
                    'amount':abs((rec.product_qty - rec.qty_received)*rec.price_unit),
                    'back_order_id':res.id,
                    'cancel_order': True
                }
                self.env['back.order.line'].create(line)
                move_flag = False


    def get_result_supplier(self,res,result):
            order_flag = True
            move_flag = False
            line = {}

            for rec in result:
                for order_line in rec.order_line:
                    for move in order_line.move_ids:
                        if move.state == 'assigned':
                            move_flag = True
                    if move_flag == True:
                        if order_flag == True:
                            line={                        
                                'supplier':rec.partner_id.name,
                                'quatation_id':rec.id,
                                'date_po':rec.date_order,
                                'code':order_line.product_id.default_code,
                                'product':order_line.product_id.name,
                                'category': order_line.product_id.product_tmpl_id.categ_id.name,
                                'quanity':abs(order_line.product_qty - order_line.qty_received),
                                'amount':abs((order_line.product_qty - order_line.qty_received)*order_line.price_unit),
                                'back_order_id':res.id,
                                'cancel_order': True
                            }
                            self.env['back.order.line'].create(line)
                            order_flag = False
                        else:
                            line={                    
                                'quatation_id':rec.id,    
                                'code':order_line.product_id.default_code,
                                'product':order_line.product_id.name,
                                'category': order_line.product_id.product_tmpl_id.categ_id.name,
                                'quanity':abs(order_line.product_qty - order_line.qty_received),
                                'amount':abs((order_line.product_qty - order_line.qty_received)*order_line.price_unit),
                                'back_order_id':res.id,
                                'cancel_order': False
                            }                       
                            self.env['back.order.line'].create(line)
                    move_flag = False
                order_flag = True

    def download_file_report_backs(self):
        url = self.generate_report_backs()
        return {
			'type': 'ir.actions.act_url',
			'url': url,
			'target': 'self',
		}

    def close_back_order(self):       
        for rec in self.lines_ids:
            if rec.quatation_id:
                for picking in rec.quatation_id.picking_ids:
                    if picking.state == 'assigned':
                        # En Odoo 15, usar action_cancel() en el picking
                        picking.action_cancel()

    def get_info_product_supplier(self,vals):
        purchase_list = []
        purchase_ids = None

        purchase_ids = self.env['purchase.order'].search([('date_order','>=',vals.get('initial_date')),('date_order','<=',vals.get('final_date')),('partner_id','=',vals.get('partner_id')[0][2])], order="partner_id asc")
        if purchase_ids:
            for purchase in purchase_ids:                
                for order in purchase.order_line:
                    for product in vals.get('product_ids')[0][2]:
                        if product == order.product_id.id:
                            purchase_list.extend(order)
        return purchase_list

    def get_info_by_product(self,vals):
        purchase_list = []
        if len(vals.get('product_ids')) >= 1 :
            for product in vals.get('product_ids')[0][2]:
                purchase_ids = self.env['purchase.order.line'].search([('date_order','>=',vals.get('initial_date')),('date_order','<=',vals.get('final_date')),('product_id','=',product)])
                if purchase_ids:
                    purchase_list.extend(purchase_ids)

        if vals.get('all_products'):
            purchase_list = self.env['purchase.order.line'].search([('date_order','>=',vals.get('initial_date')),('date_order','<=',vals.get('final_date'))])            

        return purchase_list

    def get_info_purchase(self,vals):
        purchase_ids = None

        if len(vals.get('partner_id')) >= 1:
            purchase_ids = self.env['purchase.order'].search([('date_order','>=',vals.get('initial_date')),('date_order','<=',vals.get('final_date')),('partner_id','=',vals.get('partner_id')[0][2])], order="partner_id asc")  
        if vals.get('all_supplier'):
            purchase_ids = self.env['purchase.order'].search([('date_order','>=',vals.get('initial_date')),('date_order','<=',vals.get('final_date'))], order="partner_id asc")

        return purchase_ids

    def get_info_purchase_excel(self):
        
        if self.partner_id:
            purchase_ids = self.env['purchase.order'].search([('date_order','>=',self.initial_date),('date_order','<=',self.final_date),('partner_id','=',self.partner_id.id)])
        else:
            purchase_ids = self.env['purchase.order'].search([('date_order','>=',self.initial_date),('date_order','<=',self.final_date)])
        return purchase_ids

    def update_lines(self):
        
        order_list = []
        for line in self.lines_ids:
            if line.quatation_id:
                for order_line in line.quatation_id.order_line:
                    for move_line in order_line.move_ids:
                        if move_line.state == 'cancel':
                            order_list.extend(order_line)
        
        for order_line in order_list:
            for line in self.lines_ids:
                if order_line.order_id == line.quatation_id:
                    line.hide_line = True


    def generate_report_backs(self):
        
        report_name = "Reporte back order"
		
        import ipdb; ipdb.set_trace()

		# crear libro de trabajo con hoja de trabajo
        fp = BytesIO()
        book = xlsxwriter.Workbook(fp)
        sheet = book.add_worksheet()

        #Formatos para las letras
        #Company_format
        company_format = book.add_format()
        company_format.set_bold()
        company_format.set_font_color('blue')
        company_format.set_align('center')
        #Header_format
        header_format = book.add_format()
        header_format.set_align('center')
        #Header_format
        left_format = book.add_format()
        left_format.set_align('left')
        #bold_format
        bold_format = book.add_format()
        bold_format.set_align('center')
        bold_format.set_bold()
        #Result_format
        result_format = book.add_format()
        result_format.set_align('center')
        #Formatdate
        formatdate = book.add_format({'num_format': 'dd/mm/yyyy'})
        #Currency_format
        currency_format = book.add_format({'num_format': '$#,##0.00'})
        #Total_border_format
        total_border_format = book.add_format({'num_format': '$#,##0.00'})
        total_border_format.set_border(5)
        total_border_format.set_bold()

        sheet.set_column_pixels(7, 7, 90)
        sheet.set_column_pixels(6, 6, 50)
        sheet.set_column_pixels(5, 5, 100)
        sheet.set_column_pixels(4, 4, 200)
        sheet.set_column_pixels(3, 3, 120)
        sheet.set_column_pixels(2, 2, 100)
        sheet.set_column_pixels(1, 1, 70)
        sheet.set_column_pixels(0, 0, 200)

        sheet.write(0,1,f'Reporte Back order {self.initial_date} a {self.final_date}')
        sheet.write(1,0,'Proveedor')
        sheet.write(1,1,'PO')
        sheet.write(1,2,'Fecha de pedido')
        sheet.write(1,3,'Referencia interna')
        sheet.write(1,4,'Productos')
        sheet.write(1,5,'Categoria')
        sheet.write(1,6,'Cantidad')
        sheet.write(1,7,'Precio Total')

        pointer = 3

        for rec in self.lines_ids:

            sheet.write(pointer,0,rec.supplier or ' ')
            sheet.write(pointer,1,rec.quatation_id.name or ' ')
            sheet.write(pointer,2,rec.date_po or ' ')
            sheet.write(pointer,3,rec.code or ' ')
            sheet.write(pointer,4,rec.product or ' ')
            sheet.write(pointer,5,rec.category)
            sheet.write(pointer,6,rec.quanity)
            sheet.write(pointer,7,rec.amount)
            pointer +=1

        book.close()

        out=base64.encodebytes(fp.getvalue())
        filename = "Reporte back order"
        self.write({'datas': out, 'datas_fname': filename})
        fp.close()
        url = f"/web/content/{self._name}/{self.id}/datas/{self.datas_fname}?download=true"
        return url

class ProductNackOrderLine(models.Model):
    _name = 'back.order.line'

    supplier = fields.Char(string = 'Proveedor')
    quatation_id = fields.Many2one(comodel_name='purchase.order',string='Factura')
    date_po = fields.Datetime(string = 'Fecha pedido')
    code = fields.Char(string = 'Referencia interna')
    product = fields.Char(string = 'Producto')
    category = fields.Char(string = 'Categoria')
    quanity = fields.Char(string = 'Cantidad')
    amount = fields.Char(string = 'Monto')
    back_order_id = fields.Many2one(comodel_name='product.report.back')
    hide_line = fields.Boolean(string = '')
    cancel_order = fields.Boolean(string = 'Cerrar back order')

    def close_back_order_line(self):       
        for rec in self:
            if rec.quatation_id:
                for picking in rec.quatation_id.picking_ids:
                    if picking.state == 'assigned':
                        # En Odoo 15, usar action_cancel() en el picking
                        picking.action_cancel()
                        return True    
