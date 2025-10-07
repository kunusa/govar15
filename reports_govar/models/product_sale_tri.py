# -*- coding: utf-8 -*-

from odoo import models, api, fields
import logging
import base64
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

try:
	import xlsxwriter
except ImportError:
	_logger.warning("Cannot import xlsxwriter")
	xlsxwriter = False

class productSalesWizard(models.TransientModel):

    _name = 'product.sales.report'

    datas = fields.Binary('File', readonly=True)
    datas_fname = fields.Char('Filename', readonly=True)
    date_start = fields.Date('Fecha')

    def download_trimestral_sales(self):

        self.create_and_send_excel()
        

    def generate_report(self):

        date_today = date.today()
        date_today = date_today.strftime("%d/%m/%Y")

        # crear libro de trabajo con hoja de trabajo

        book = xlsxwriter.Workbook('/tmp/sample.xlsx')
        sheet = book.add_worksheet('1er periodo')
        sheet2 = book.add_worksheet('2do periodo')
        sheet3 = book.add_worksheet('3ro periodo')
        sheet4 = book.add_worksheet('4to periodo')


        submint = "Reporte ventas trimestrales {} {}".format(self.env.cr.dbname,date_today)
        
        #Primer periodo
        sheet.write(1,0,'Codigo')
        sheet.write(1,1,'Producto')
        sheet.write(1,2,'Precio unitario')
        sheet.write(1,3,'Cantidad')
        sheet.write(1,4,'Inventario')

        sheet.set_column('A:A', 160/7)
        sheet.set_column('B:B', 250/7)
        sheet.set_column('C:C', 50/7)
        sheet.set_column('D:D', 50/7)
        sheet.set_column('E:E', 50/7)

        #Segundo periodo
        sheet2.write(1,0,'Codigo')
        sheet2.write(1,1,'Producto')
        sheet2.write(1,2,'Precio unitario')
        sheet2.write(1,3,'Cantidad')
        sheet2.write(1,4,'Inventario')

        sheet2.set_column('A:A', 160/7)
        sheet2.set_column('B:B', 250/7)
        sheet2.set_column('C:C', 50/7)
        sheet2.set_column('D:D', 50/7)
        sheet2.set_column('E:E', 50/7)

        #Tercer periodo       
        sheet3.write(1,0,'Codigo')
        sheet3.write(1,1,'Producto')
        sheet3.write(1,2,'Precio unitario')
        sheet3.write(1,3,'Cantidad')
        sheet3.write(1,4,'Inventario')

        sheet3.set_column('A:A', 160/7)
        sheet3.set_column('B:B', 250/7)
        sheet3.set_column('C:C', 50/7)
        sheet3.set_column('D:D', 50/7)
        sheet3.set_column('E:E', 50/7)

        #Cuarto periodo
        sheet4.write(1,0,'Codigo')
        sheet4.write(1,1,'Producto')
        sheet4.write(1,2,'Precio unitario')
        sheet4.write(1,3,'Cantidad')
        sheet4.write(1,4,'Inventario')

        sheet4.set_column('A:A', 160/7)
        sheet4.set_column('B:B', 250/7)
        sheet4.set_column('C:C', 50/7)
        sheet4.set_column('D:D', 50/7)
        sheet4.set_column('E:E', 50/7)

        pointer = 1
        num_periodos = 5
        count = 0
        fechas = []
        periodos = []

        if self.date_start:
            initial_date = self.date_start
        else:
            today = date.today()
            initial_date = datetime(today.year, today.month, today.day, 0, 0)            

        # Calcular las fechas
        for i in range(num_periodos):
            fecha = initial_date - relativedelta(months=3 * i)
            fechas.append(fecha.strftime("%Y-%m-%d"))
        fechas.reverse()

        #Generar titulos 

        sheet.merge_range('A1:E1',"Periodo de {} a {} ".format(fechas[0],fechas[1]))
        sheet2.merge_range('A1:E1',"Periodo de {} a {} ".format(fechas[1],fechas[2]))
        sheet3.merge_range('A1:E1',"Periodo de {} a {} ".format(fechas[2],fechas[3]))
        sheet4.merge_range('A1:E1',"Periodo de {} a {} ".format(fechas[3],fechas[4]))

        for i in range(4):
            query = """
                SELECT 
                    pp.id,
                    pt.default_code AS codigo,
                    pt."name",
                    SUM(ail.price_unit ) AS precio_unitario,
                    SUM(ail.quantity) AS cantidad_total 
                FROM account_move AS ai           
                JOIN account_move_line AS ail ON ai.id = ail.move_id            
                JOIN product_product AS pp ON ail.product_id = pp.id    
                JOIN product_template AS pt ON pp.product_tmpl_id = pt.id
                WHERE  
                    ai.move_type = 'out_invoice' 
                    AND ai.state = 'posted'
                    AND ai.invoice_date BETWEEN '{}' AND '{}'
                GROUP BY pp.id,pt.default_code, pt."name"
                ORDER BY pt."name";
            """.format(fechas[count],fechas[i+1])
            self.env.cr.execute(query)
            result_dict = self.env.cr.dictfetchall()
            periodos.append(result_dict)
            count += 1

        for rec in periodos[0]:
            pointer += 1
            sheet.write(pointer,0,rec.get('codigo'))
            sheet.write(pointer,1,rec.get('name'))
            sheet.write(pointer,2,rec.get('precio_unitario'))
            sheet.write(pointer,3,rec.get('cantidad_total'))
            sheet.write(pointer,4,self.get_inevntory(rec.get('id')))
        pointer = 1
        for rec in periodos[1]:
            pointer += 1
            sheet2.write(pointer,0,rec.get('codigo'))
            sheet2.write(pointer,1,rec.get('name'))
            sheet2.write(pointer,2,rec.get('precio_unitario'))
            sheet2.write(pointer,3,rec.get('cantidad_total'))
            sheet2.write(pointer,4,self.get_inevntory(rec.get('id')))
        pointer = 1
        for rec in periodos[2]:
            pointer += 1
            sheet3.write(pointer,0,rec.get('codigo'))
            sheet3.write(pointer,1,rec.get('name'))
            sheet3.write(pointer,2,rec.get('precio_unitario'))
            sheet3.write(pointer,3,rec.get('cantidad_total'))
            sheet3.write(pointer,4,self.get_inevntory(rec.get('id')))
        pointer = 1
        for rec in periodos[3]:
            pointer += 1
            sheet4.write(pointer,0,rec.get('codigo'))
            sheet4.write(pointer,1,rec.get('name'))
            sheet4.write(pointer,2,rec.get('precio_unitario'))
            sheet4.write(pointer,3,rec.get('cantidad_total'))
            sheet4.write(pointer,4,self.get_inevntory(rec.get('id')))
       
        book.close()

        return '/tmp/sample.xlsx',submint

    def create_and_send_excel(self):
        # Crear el archivo Excel

        file_path,submint = self.generate_report()

        # Adjuntar el archivo al registro
        attachment = self.attach_file_to_record(file_path,submint)

        # Enviar el correo electrónico con el archivo adjunto
        self.send_email_with_attachment(attachment,submint)

        return True
    

    def attach_file_to_record(self, file_path,submint):
        with open(file_path, 'rb') as file:
            file_data = file.read()

        attachment = self.env['ir.attachment'].create({
            'name': f'{submint}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data).decode('utf-8'),
        })
        
    
        return attachment
    
    def send_email_with_attachment(self, attachment,submint):
        import ipdb; ipdb.set_trace()
        mail = self.env['mail.mail'].create({
            'subject': submint,
            'body_html': '<p>Envio de excel adjunto con las ventas trimestrales.</p>',
            'email_from': self.env.user.company_id.email,
            'email_to': self.env['ir.config_parameter'].sudo().get_param('email_sales', ''),
            'attachment_ids': [(6, 0, [attachment.id])]
        })
        mail.send()



    def get_inevntory(self,product_id):
         
        query = '''
        SELECT COALESCE(SUM(sq.quantity), 0) AS quantity
        FROM product_product pp
        LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
        LEFT JOIN stock_quant sq ON pp.id = sq.product_id AND sq.location_id IN (
            SELECT id FROM stock_location WHERE "usage" = 'internal' AND active = TRUE
        )
        WHERE pt.type IN ('consu', 'product') AND pt.active = TRUE and pp.id = {};
        '''.format(product_id)
         
        self.env.cr.execute(query)
        result_dict = self.env.cr.dictfetchall()

        return result_dict[0].get('quantity')
