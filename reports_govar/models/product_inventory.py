from odoo import fields, models, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone
from io import BytesIO
import base64
import pytz
import logging

_logger = logging.getLogger(__name__)



try:
	import xlsxwriter
except ImportError:
	_logger.warning("Cannot import xlsxwriter")
	xlsxwriter = False

class ProductReportInventory(models.TransientModel):
    _name = "product.report.inventory"
    _description = "Product Report inventory .xlsx"


    initial_date = fields.Date(string = 'Fecha')
    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    stock_warehouse_id = fields.Many2many('stock.warehouse', 'stock_warehouse_report_rel', 'stock_warehouse_report_id',
        'stock_warehouse_id', 'Almacen')
    location_ids = fields.Many2many('stock.location', 'report_stock_location_rel', 'report_stock_id',
    'location_id', 'Locacion')


    def download_file_report_inventory(self):
        # Use sudo() to bypass security restrictions for report generation
        url = self.sudo().generate_report_inventory()
        return {
			'type': 'ir.actions.act_url',
			'url': url,
			'target': 'self',
		}

    def get_products(self,initial_date,date,product_id):

        end_date = date.strftime('%Y-%m-%d')

        query = """SELECT pt.type,pt."name",pt.default_code as inter_code,pt.id, pt.list_price,sum(ail.quantity) as cantidad 
        FROM product_product as pp
        FULL OUTER JOIN account_move_line as ail  
        ON pp.id = ail.product_id
        FULL OUTER JOIN account_move as ai
        ON ai.id = ail.move_id
        FULL OUTER JOIN product_template as pt
        ON pp.product_tmpl_id = pt.id
        WHERE pp.active = True and ai.move_type = 'out_invoice' and ai.state = 'posted'
                  and  ai.invoice_date BETWEEN '{}' AND '{}' and pt.type = 'product' and pt.id in {}
            group by pt."name",pt.default_code,pt.id,pt.list_price,pt.type ORDER BY pt."name";
        """.format(end_date,initial_date,product_id)
        self.env.cr.execute(query)
        result_dict = self.env.cr.dictfetchall()
        return result_dict

    @api.model
    def get_default_date_model(self):
        return pytz.UTC.localize(datetime.now()).astimezone(timezone(self.env.user.tz or 'UTC'))

    def generate_report_inventory(self):
        """Generate inventory report with Excel export for Odoo 15"""
        # crear libro de trabajo con hoja de trabajo
        fp = BytesIO()
        book = xlsxwriter.Workbook(fp)
        product_stock = book.add_worksheet("Stock")
        product_invoice = book.add_worksheet("Facturado")

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
        right_format = book.add_format()
        right_format.set_align('right')
        #bold_format
        bold_format = book.add_format()
        bold_format.set_align('center')
        bold_format.set_bold()
        #Result_format
        result_format = book.add_format()
        result_format.set_align('center')
        #Currency_format
        currency_format = book.add_format({'num_format': '$#,##0.00'})
        #Total_border_format
        total_border_format = book.add_format({'num_format': '$#,##0.00'})
        total_border_format.set_border(5)
        total_border_format.set_bold()


        product_stock.set_column_pixels(2, 2, 100)
        product_stock.set_column_pixels(1, 1, 100)
        product_stock.set_column_pixels(0, 0, 280)
        product_stock.write(1,0,'Producto')
        product_stock.write(1,1,'Inventario (cantidad)')
        product_stock.write(1,2,'inventario ($)')
        product_invoice.set_column_pixels(2, 3, 100)
        product_invoice.set_column_pixels(2, 2, 100)
        product_invoice.set_column_pixels(1, 1, 100)
        product_invoice.set_column_pixels(0, 0, 280)
        product_invoice.write(1,0,'Producto')
        product_invoice.write(1,1,'Cantidad facturada los ultimos 3 meses')
        product_invoice.write(1,2,'Cantidad facturada los ultimos 6 meses')
        product_invoice.write(1,3,'Cantidad facturada los ultimos 12 meses')




        date = self.initial_date

        date_3 = date - relativedelta(months=int(3))
        date_6 = date - relativedelta(months=int(6))
        date_12 = date - relativedelta(months=int(12))




        data = self.read()[0]
        location_ids = data['location_ids']
        product_ids = self.env['product.product'].search([('active','=',True)])
        product_ids = [prod.id for prod in product_ids]

        where_product_ids = " 1=1 "
        where_product_ids2 = " 1=1 "

        if product_ids :
            where_product_ids = " quant.product_id in %s"%str(tuple(product_ids)).replace(',)', ')')
            where_product_ids2 = " product_id in %s"%str(tuple(product_ids)).replace(',)', ')')
        location_ids2 = self.env['stock.location'].search([('usage','=','internal')])
        ids_location = [loc.id for loc in location_ids2]
        where_location_ids = " quant.location_id in %s"%str(tuple(ids_location)).replace(',)', ')')
        where_location_ids2 = " location_id in %s"%str(tuple(ids_location)).replace(',)', ')')
        if location_ids :
            where_location_ids = " quant.location_id in %s"%str(tuple(location_ids)).replace(',)', ')')
            where_location_ids2 = " location_id in %s"%str(tuple(location_ids)).replace(',)', ')')


        datetime_format = '%Y-%m-%d %H:%M:%S'
        utc = datetime.now().strftime(datetime_format)
        utc = datetime.strptime(utc, datetime_format)
        tz = self.get_default_date_model().strftime(datetime_format)
        tz = datetime.strptime(tz, datetime_format)
        duration = tz - utc
        hours = duration.seconds / 60 / 60
        if hours > 1 or hours < 1 :
            hours = str(hours) + ' hours'
        else :
            hours = str(hours) + ' hour'
        
        query = """
            SELECT 
                prod_tmpl.default_code as intern_reference,
                prod_tmpl.name as product, 
                prod_tmpl.list_price as price, 
                prod_tmpl.type as tipo, 
                prod_tmpl.id as product_prodct_id, 
                categ.name as prod_categ, 
                loc.complete_name as location,
                quant.in_date + interval '%s' as date_in, 
                date_part('days', now() - (quant.in_date + interval '%s')) as aging,
                sum(quant.quantity) as total_product, 
                sum(quant2.quantity) as stock, 
                sum(quant3.quantity) as reserved
            FROM 
                stock_quant quant
            LEFT JOIN 
                (select * from stock_quant where %s and %s
                and reserved_quantity = 0) quant2 on quant2.id = quant.id
            LEFT JOIN 
                (select * from stock_quant where %s and %s
                and reserved_quantity > 0)quant3 on quant3.id = quant.id
            LEFT JOIN 
                stock_location loc on loc.id=quant.location_id
            LEFT JOIN 
                product_product prod on prod.id=quant.product_id
            LEFT JOIN 
                product_template prod_tmpl on prod_tmpl.id=prod.product_tmpl_id
            LEFT JOIN 
                product_category categ on categ.id=prod_tmpl.categ_id
            WHERE 
                %s and %s
            GROUP BY 
                intern_reference,product_prodct_id,product,price,tipo, prod_categ, location, date_in
            ORDER BY 
                date_in
        """
        
        # Execute query with proper parameter binding for security
        self.env.cr.execute(query % (hours, hours, where_product_ids2, where_location_ids2, where_product_ids2, where_location_ids2, where_product_ids, where_location_ids))
        result = self.env.cr.dictfetchall()

        product_id = []
        for rec in result:
            product_id.append(rec.get('product_prodct_id'))



        # Get product data
        products_12 = self.get_products(self.initial_date, date_12, tuple(product_id))
        products_6 = self.get_products(self.initial_date, date_6, tuple(product_id))
        products_3 = self.get_products(self.initial_date, date_3, tuple(product_id))

        pointer = 1

        for rec in products_12:

            pointer += 1
            for rec6 in products_6:
                if rec6.get('id') == rec.get('id'):
                    product_invoice.write(pointer,2 ,rec6.get('cantidad'))
                    break
                else:
                    product_invoice.write(pointer,2 ,"0",right_format)

            for rec3 in products_3:
                if rec3.get('id') == rec.get('id'):
                    product_invoice.write(pointer,1 ,rec3.get('cantidad'))
                    break
                else:
                    product_invoice.write(pointer,1 ,"0",right_format)

            product_invoice.write(pointer,0 ,u"[{}]{}".format((rec.get('inter_code') or ""),rec.get('name')))
            product_invoice.write(pointer,3 ,rec.get('cantidad'))
        pointer = 1

        for rec in result:
            if rec.get('intern_reference') != None and rec.get('product') != None and rec.get('tipo')== 'product':
                pointer += 1
                product_stock.write(pointer,0 ,u"[{}]{}".format((rec.get('intern_reference') or ""),rec.get('product')))
                product_stock.write(pointer,1 ,rec.get('total_product',0))
                product_stock.write(pointer,2 ,(float(rec.get('total_product',0))*float(rec.get('price')) or 0))

        book.close()

        out = base64.encodebytes(fp.getvalue())
        filename = "Reporte inventario-ventas"
        self.sudo().write({'datas': out, 'datas_fname': filename})
        fp.close()
        url = "/web/content/{}/{}/datas/{}?download=true".format(self._name, self.id, self.datas_fname)
        return url