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


class ProductReportStock(models.TransientModel):
    _name = "product.report.stock"
    _description = "Product Report .xlsx"


    initial_date = fields.Date(string = 'Desde')
    final_date = fields.Date(string = 'Hasta')
    compare_initial_date = fields.Date(string = 'Desde')
    compare_final_date = fields.Date(string = 'Hasta')
    all_products = fields.Boolean(string = 'Todos los productos')
    product_category_id = fields.Many2many('product.category', 'product_report_sell_categ_rel', 'product_report_sell_id',
        'categ_id', 'Categorias')
    product_category = fields.Boolean(string='Por categoria')
    product_product = fields.Boolean(string = 'Por productos')
    client_partner = fields.Boolean(string = 'Por clientes')
    flag_product = fields.Boolean(string = '')
    flag_product_product = fields.Boolean(string = '')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    partner_ids = fields.Many2many('res.partner', 'partner_report_sell_rel', 'partner_report_sell_id',
        'partner_id', 'Clientes')
    product_ids = fields.Many2many('product.product', 'product_report_sell_prod_rel', 'product_report_sell_id',
        'product_id', 'Productos')


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

    def get_invoice_sales(self, start_date,end_date,type_invoice):
        facturas_ids = []
        query = """
            select id from account_payment where partner_type = '{}' and state = 'posted' and (payment_date) BETWEEN '{}' AND '{}' ;
        """.format(type_invoice,start_date,end_date)
        self.env.cr.execute(query)
        result_dict = self.env.cr.fetchall()

        for pago_id in result_dict:
            payment_id = self.env['account.payment'].search([('id','=',pago_id[0])])
            # In Odoo 15, invoice_ids is replaced with move_id for single invoice or move_ids for multiple
            if hasattr(payment_id, 'move_id') and payment_id.move_id:
                facturas_ids.append(payment_id.move_id.id)
            elif hasattr(payment_id, 'move_ids'):
                facturas_ids += payment_id.move_ids.ids

        factura_ids = self.env['account.move'].search([('id','in',facturas_ids)])

        return factura_ids

    def download_file_report_sales(self):
        url = self.generate_report()
        return {
			'type': 'ir.actions.act_url',
			'url': url,
			'target': 'self',
		}

    def get_info_sales(self,query_str,start_date,end_date):
        query = """
            SELECT rp.name as cliente,ai.name as factura,pt.default_code as codigo,pt."name",pc."name" as categoria,ail.price_unit as monto, ail.quantity as cantidad 
            FROM account_move as ai           
            JOIN account_move_line as ail            
            ON ai.id = ail.move_id            
            JOIN product_product as pp            
            ON ail.product_id = pp.id    
            join product_template as pt
            on pp.product_tmpl_id = pt.id
            join res_partner as rp
            on ai.partner_id = rp.id
            join product_category as pc
            on pt.categ_id = pc.id
            WHERE {}  ai.move_type = 'out_invoice' and ai.state = 'posted'
                  and  ai.invoice_date BETWEEN '{}' AND '{}'
            group by pt.default_code,ail.price_unit,pt."name",pc."name",ail.quantity,ai.name,rp.name;
        """.format(query_str,start_date,end_date)
        self.env.cr.execute(query)
        result_dict = self.env.cr.dictfetchall()
        return result_dict



    def generate_report(self):
        

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

        sheet.set_column_pixels(6, 6, 200)#cliente
        sheet.set_column_pixels(5, 5, 100)#factura
        sheet.set_column_pixels(4, 4, 100)#cantidad
        sheet.set_column_pixels(3, 3, 100)#monto
        sheet.set_column_pixels(2, 2, 100)#categoria
        sheet.set_column_pixels(1, 1, 380)#producto
        sheet.set_column_pixels(0, 0, 100)#codigo
        sheet.merge_range('A1:F1','Productos vendidos {} a {}'.format(self.initial_date,self.final_date),result_format)
        sheet.write(0,1,'Reporte de productos vendidos {} a {}'.format(self.initial_date,self.final_date))
        sheet.write(1,0,'Codigo')
        sheet.write(1,1,'Producto')
        sheet.write(1,2,'Categoria')
        sheet.write(1,3,'Monto')
        sheet.write(1,4,'Cantidad')
        sheet.write(1,5,'Factura')
        sheet.write(1,6,'Cliente')


        if self.compare_final_date and self.compare_initial_date:
            sheet.merge_range('G1:J1','Productos vendidos {} a {}'.format(self.compare_final_date,self.compare_initial_date),result_format)
            sheet.write(1,6,'Codigo')
            sheet.write(1,7,'Producto')
            sheet.write(1,8,'Categoria')
            sheet.write(1,9,'Monto')
            sheet.write(1,10,'Cantidad')
            sheet.write(1,11,'Factura')
            sheet.write(1,12,'Cliente')
            sheet.set_column_pixels(12, 12, 200)
            sheet.set_column_pixels(11, 11, 100)
            sheet.set_column_pixels(10, 10, 100)
            sheet.set_column_pixels(9, 9, 100)
            sheet.set_column_pixels(8, 8, 100)
            sheet.set_column_pixels(7, 7, 380)
            sheet.set_column_pixels(6, 6, 100)
        pointer = 1
        query_str = ""

        if self.product_category:

            if len(self.product_category_id) > 1:
                query_str += " pt.categ_id in {} and ".format(tuple(self.product_category_id.ids))
            else:
                query_str += " pt.categ_id = {} and ".format(str(self.product_category_id.id))

        if self.product_product:
            if len(self.product_ids) > 1:
                query_str += " pp.id in {} and ".format(tuple(self.product_ids.ids))
            else:
                query_str += " pp.id = {} and ".format(str(self.product_ids.id))
               
        if self.client_partner:
            if len(self.partner_ids) > 1:
                query_str += " rp.id in {} and ".format(tuple(self.partner_ids.ids))
          
            else:
                query_str += " rp.id = {} and ".format(str(self.partner_ids.id))
                
        result_dict = self.get_info_sales(query_str,self.initial_date,self.final_date)                  
        
        for rec in result_dict:
            pointer += 1
            sheet.write(pointer,0,rec.get('codigo'))
            sheet.write(pointer,1,rec.get('name'))
            sheet.write(pointer,2,rec.get('categoria'))
            sheet.write(pointer,3,rec.get('monto'),currency_format)
            sheet.write(pointer,4,rec.get('cantidad'),result_format)
            sheet.write(pointer,5,rec.get('factura')) 
            sheet.write(pointer,6,rec.get('cliente'))          

        if self.compare_final_date and self.compare_initial_date:
           

            if self.product_category:
                if len(self.product_category_id) > 1:
                    query_str = "pt.categ_id in "
                    query_str += " pt.categ_id in {} and ".format(tuple(self.product_category_id.ids))
                else:
                    query_str = " pt.categ_id = {} and ".format(str(self.product_category_id.id))
                    
            if self.product_product:
                if len(self.product_ids) > 1:
                    query_str += " pp.id in {} and ".format(tuple(self.product_ids.ids))
                else:
                    query_str = " pp.id = {} and ".format(str(self.product_ids.id))
                               
            if self.client_partner:
                if len(self.partner_ids) > 1:
                    query_str += " rp.id in {} and ".format(tuple(self.partner_ids.ids))
            
                else:
                    query_str += " rp.id = {} and ".format(str(self.partner_ids.id))

            result_dict = self.get_info_sales(query_str,self.compare_initial_date,self.compare_final_date)

            pointer = 1

            for rec in result_dict:

                pointer += 1
                sheet.write(pointer,6,rec.get('codigo'))
                sheet.write(pointer,7,rec.get('name'))
                sheet.write(pointer,8,rec.get('categoria'))
                sheet.write(pointer,9,rec.get('monto'),currency_format)
                sheet.write(pointer,10,rec.get('cantidad'),result_format)
                sheet.write(pointer,11,rec.get('factura')) 
                sheet.write(pointer,12,rec.get('cliente')) 

        book.close()

        out=base64.encodebytes(fp.getvalue())
        filename = "Reporte de productos"
        self.write({'datas':out, 'datas_fname':filename})
        fp.close()
        url = "/web/content/{}/{}/datas/{}?download=true".format(self._name, self.id, self.datas_fname)
        return url
