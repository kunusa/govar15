from odoo import fields, models, api
from io import BytesIO
import logging
import base64


_logger = logging.getLogger(__name__)
try:
	import xlsxwriter
except ImportError:
	_logger.warning("Cannot import xlsxwriter")
	xlsxwriter = False


class ProductStockBuys(models.Model):
    _name = "report.stock.buys"
    _rec_name = 'code_report'

    code_report = fields.Char(string='Folio',readonly=True)
    initial_date = fields.Date(string = 'Desde')
    final_date = fields.Date(string = 'Hasta')
    compare_initial_date = fields.Date(string = 'Desde')
    compare_final_date = fields.Date(string = 'Hasta')
    supplier_flag = fields.Boolean(string = 'Por Provedor')
    product_category_id = fields.Many2many('product.category', 'product_report_buys_categ_rel', 'product_report_buys_id',
        'categ_id', 'Categorias')
    product_category = fields.Boolean(string='Por categoria')
    product_product = fields.Boolean(string = 'Por producto')
    flag_product = fields.Boolean(string = '')
    flag_product_product = fields.Boolean(string = '')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    product_ids = fields.Many2many('product.product', 'product_report_buys_rel', 'product_report_buys_id',
        'product_id', 'Productos')
    lines_ids = fields.One2many(comodel_name='report.stock.line',inverse_name='stock_report_id',string='Lineas de productos')
    lines_compare_ids = fields.One2many(comodel_name='report.stock.compare.line',inverse_name='stock_report_id',string='Comparacion')
    partner_id = fields.Many2many('res.partner', 'supplier_report_buys_rel', 'supplier_report_buys_id',
        'partner_id', 'Proveedor',domain=[('supplier_rank','>=',0)])
    reference = fields.Char(string = 'Referencia proveedor')
    invoice_id = fields.Many2many('account.move', 'invoice_report_buys_rel', 'invoice_report_buys_id',
        'invoice_id', 'Factura',domain=[('move_type','=','in_invoice')])

    @api.model
    def create(self, vals):
        vals['code_report'] = self.env['ir.sequence'].next_by_code('report.stock.buys') or 'Nuevo'
        res = super(ProductStockBuys,self).create(vals)
        result = self.get_info_products(vals)
        line={}
        for rec in result:
            line={
            'code':rec.get('codigo'),
			'product':rec.get('name'),
			'amount':rec.get('monto'),
			'quanity':rec.get('cantidad'),
			'invoice_id':rec.get('invoice_id'),
            'supplier':rec.get('cliente'),
            'stock_report_id':res.id
			}
            self.env['report.stock.line'].create(line)

        if vals.get('compare_final_date') and vals.get('compare_final_date'):
            result = self.get_info_products_compare(vals)
            for rec in result:
                line={
                'code':rec.get('codigo'),
                'product':rec.get('name'),
                'amount':rec.get('monto'),
                'quanity':rec.get('cantidad'),
                'invoice_id':rec.get('invoice_id'),
                'supplier':rec.get('cliente'),
                'stock_report_id':res.id
                }
                self.env['report.stock.compare.line'].create(line)

        return res

    @api.onchange('product_category')
    def type_of_product(self):

        if self.product_category:
            self.flag_product = True
        else:
            self.flag_product = False

    @api.onchange('product_product')
    def type_of_product_product(self):

        if self.product_product:
            self.flag_product_product = True
        else:
            self.flag_product_product = False

    def download_file_report_buys(self):
        # Use sudo() to bypass security restrictions for report generation
        url = self.sudo().generate_report_buys()
        return {
			'type': 'ir.actions.act_url',
			'url': url,
			'target': 'self',
		}

    def get_info_buys(self,query_str,start_date,end_date):
        query = """
            SELECT ai.id as invoice_id,rp.name as cliente,ai.name as factura,pt.default_code as codigo,pt."name",ail.price_unit as monto, ail.quantity as cantidad 
            FROM account_move as ai           
            JOIN account_move_line as ail            
            ON ai.id = ail.move_id            
            JOIN product_product as pp            
            ON ail.product_id = pp.id    
            join product_template as pt
            on pp.product_tmpl_id = pt.id
            join res_partner as rp
            on ai.partner_id = rp.id
            WHERE {}  ai.move_type = 'in_invoice' and ai.state = 'posted'
                  and  ai.invoice_date BETWEEN '{}' AND '{}'
            group by ai.id,pt.default_code,ail.price_unit,pt."name",ail.quantity,ai.name,rp.name;
        """.format(query_str,start_date,end_date)
        self.env.cr.execute(query)
        result_dict = self.env.cr.dictfetchall()
        return result_dict



    def get_info_products_compare(self,vals):
        query_str = ""
        if vals.get('product_category'):

            if len(vals.get('product_category_id')[0][2]) > 1:
                query_str = "pt.categ_id in "
                query_str += " {} and".format(tuple(vals.get('product_category_id')[0][2]))
            else:
                id = ''.join(map(str,tuple(vals.get('product_category_id')[0][2])))
                query_str += "pt.categ_id = {} and".format(id)


        if vals.get('product_product'):
            if len(vals.get('product_ids')[0][2]) > 1:
                query_str = "pp.id in " 
                query_str += " {} and".format(tuple(vals.get('product_ids')[0][2]))
            else:
                id = ''.join(map(str,tuple(vals.get('product_ids')[0][2])))
                query_str += "pp.id = {} and".format(id)

        if vals.get('supplier_flag'):
            if vals.get('partner_id'):
                if len(vals.get('partner_id')[0][2]) > 1:
                    query_str = " ai.partner_id in "
                    query_str += " {} and".format(tuple(vals.get('partner_id')[0][2]))
                else:
                    id = ''.join(map(str,tuple(vals.get('partner_id')[0][2])))
                    query_str += "ai.partner_id = {} and".format(id)
            if vals.get('reference'):
                reference_list = vals.get('reference').split(",")
                reference = map(str, reference_list)
                if len(reference) > 1:
                    tuple_reference = tuple(reference)
                    query_str = " ai.reference in "
                    query_str += " {} and".format(tuple_reference)
                else:
                    query_str = " ai.reference = "
                    query_str += " '{}' and".format(vals.get('reference'))                    

        result_dict = self.get_info_buys(query_str,vals.get('compare_initial_date'),vals.get('compare_final_date'))   
        return result_dict

    def get_info_products(self,vals):
        query_str = ""
        if vals.get('product_category'):

            if len(vals.get('product_category_id')[0][2]) > 1:
                query_str = "pt.categ_id in "
                query_str += " {} and".format(tuple(vals.get('product_category_id')[0][2]))
            else:
                id = ''.join(map(str,tuple(vals.get('product_category_id')[0][2])))
                query_str += "pt.categ_id = {} and".format(id)


        if vals.get('product_product'):
            if len(vals.get('product_ids')[0][2]) > 1:
                query_str = "pp.id in " 
                query_str += " {} and".format(tuple(vals.get('product_ids')[0][2]))
            else:
                id = ''.join(map(str,tuple(vals.get('product_ids')[0][2])))
                query_str = "pp.id = {} and".format(id)
        
        if vals.get('supplier_flag'):
            if vals.get('partner_id'):
                if len(vals.get('partner_id')[0][2]) > 1:
                    query_str = " ai.partner_id in "
                    query_str += " {} and".format(tuple(vals.get('partner_id')[0][2]))
                else:
                    id = ''.join(map(str,tuple(vals.get('partner_id')[0][2])))
                    query_str += "ai.partner_id = {} and".format(id)
            if vals.get('reference'):
                reference_list = vals.get('reference').split(",")
                reference = map(str, reference_list)
                if len(reference) > 1:
                    tuple_reference = tuple(reference)
                    query_str = " ai.reference in "
                    query_str += " {} and".format(tuple_reference)
                else:
                    query_str = " ai.reference = "
                    query_str += " '{}' and".format(vals.get('reference'))     


        result_dict = self.get_info_buys(query_str,vals.get('initial_date'),vals.get('final_date'))  
        return result_dict

    def generate_report_buys(self):
        

        report_name = "Reporte de productos"
		
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

        sheet.set_column_pixels(5, 5, 200)#cliente
        sheet.set_column_pixels(4, 4, 100)#factura
        sheet.set_column_pixels(3, 3, 100)#cantidad
        sheet.set_column_pixels(2, 2, 100)#monto
        sheet.set_column_pixels(1, 1, 380)#producto
        sheet.set_column_pixels(0, 0, 100)#codigo
        sheet.merge_range('A1:F1','Productos comprados {} a {}'.format(self.initial_date,self.final_date),result_format)
        sheet.write(0,1,'Reporte de productos comprados {} a {}'.format(self.initial_date,self.final_date))
        sheet.write(1,0,'Codigo')
        sheet.write(1,1,'Producto')
        sheet.write(1,2,'Monto')
        sheet.write(1,3,'Cantidad')
        sheet.write(1,4,'Factura')
        sheet.write(1,5,'Proveedor')


        if self.compare_final_date and self.compare_initial_date:
            sheet.merge_range('G1:J1','Productos comprados {} a {}'.format(self.compare_final_date,self.compare_initial_date),result_format)
            sheet.write(1,6,'Codigo')
            sheet.write(1,7,'Producto')
            sheet.write(1,8,'Monto')
            sheet.write(1,9,'Cantidad')
            sheet.write(1,10,'Factura')
            sheet.write(1,11,'Proveedor')
            sheet.set_column_pixels(11, 11, 200)
            sheet.set_column_pixels(10, 10, 100)
            sheet.set_column_pixels(9, 9, 100)
            sheet.set_column_pixels(8, 8, 100)
            sheet.set_column_pixels(7, 7, 380)
            sheet.set_column_pixels(6, 6, 100)
        pointer = 1

        for rec in self.lines_ids:
            pointer += 1
            sheet.write(pointer,0,rec.code)
            sheet.write(pointer,1,rec.product)
            sheet.write(pointer,2,rec.amount,currency_format)
            sheet.write(pointer,3,rec.quanity,result_format)
            # Use sudo() to access invoice name without security restrictions
            sheet.write(pointer,4,rec.invoice_id.sudo().name) 
            sheet.write(pointer,5,rec.supplier)          

        if self.compare_final_date and self.compare_initial_date:
           
            pointer = 1
            for rec in self.lines_compare_ids:
                pointer += 1
                sheet.write(pointer,6,rec.code)
                sheet.write(pointer,7,rec.product)
                sheet.write(pointer,8,rec.amount,currency_format)
                sheet.write(pointer,9,rec.quanity,result_format)
                # Use sudo() to access invoice name without security restrictions
                sheet.write(pointer,10,rec.invoice_id.sudo().name) 
                sheet.write(pointer,11,rec.supplier) 

        book.close()

        out=base64.encodebytes(fp.getvalue())
        filename = "Reporte de productos"
        self.write({'datas':out, 'datas_fname':filename})
        fp.close()
        url = "/web/content/{}/{}/datas/{}?download=true".format(self._name, self.id, self.datas_fname)
        return url



class ProductStockBuysLine(models.Model):
    _name = 'report.stock.line'

    code = fields.Char(string = 'Codigo')
    product = fields.Char(string = 'Producto')
    amount = fields.Char(string = 'Monto')
    quanity = fields.Char(string = 'Cantidad')
    invoice = fields.Char(string = 'Factura')
    supplier = fields.Char(string = 'Proveedor')
    stock_report_id = fields.Many2one(comodel_name='report.stock.buys')
    invoice_id = fields.Many2one(comodel_name='account.move',string='Factura')

class ProductStockBuysCompareLine(models.Model):
    _name = 'report.stock.compare.line'

    code = fields.Char(string = 'Codigo')
    product = fields.Char(string = 'Producto')
    amount = fields.Char(string = 'Monto')
    quanity = fields.Char(string = 'Cantidad')
    invoice = fields.Char(string = 'Factura')
    supplier = fields.Char(string = 'Proveedor')
    stock_report_id = fields.Many2one(comodel_name='report.stock.buys')
    invoice_id = fields.Many2one(comodel_name='account.move',string='Factura')