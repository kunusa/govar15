# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from io import BytesIO
import logging
import base64
from datetime import date

_logger = logging.getLogger(__name__)

try:
	import xlsxwriter
except ImportError:
	_logger.warning("Cannot import xlsxwriter")
	xlsxwriter = False


class productAvaibilityWizard(models.TransientModel):

    _name = 'product.avaibility'

    datas = fields.Binary('File', readonly=True)

    def product_avaibiliy(self):

        self.create_and_send_excel()
    
    def generate_report(self):

        date_today = date.today()
        date_today = date_today.strftime("%d/%m/%Y")
        # crear libro de trabajo con hoja de trabajo

        book = xlsxwriter.Workbook('/tmp/sample.xlsx')
        sheet = book.add_worksheet()


        submint = f"Reporte producto minimo {self.env.cr.dbname} {date_today}"

        sheet.merge_range('A1:F1',submint)
        sheet.write(0,1,f'Reporte producto minimo {self.env.cr.dbname}')
        sheet.write(1,0,'Codigo')
        sheet.write(1,1,'Producto')
        sheet.write(1,2,'Cantidad')

        sheet.set_column('A:A', 180/7)
        sheet.set_column('B:B', 250/7)
        sheet.set_column('C:C', 50/7)

        pointer = 1
    

        query = '''
            SELECT pp.id AS product_id, pt.default_code AS codigo, pt.name, COALESCE(SUM(sq.quantity), 0) AS quantity
            FROM product_product pp
            LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN stock_quant sq ON pp.id = sq.product_id AND sq.location_id IN (
                SELECT id FROM stock_location WHERE "usage" = 'internal' AND active = TRUE
            )
            WHERE pt.type IN ('consu', 'product') AND pt.active = TRUE
            GROUP BY pp.id, pt.default_code, pt.name
            HAVING COALESCE(SUM(sq.quantity), 0) <= 3;

        '''

        self.env.cr.execute(query)
        products_dict = self.env.cr.dictfetchall()

        
        for rec in products_dict:
            pointer += 1
            sheet.write(pointer,0,rec.get('codigo'))
            sheet.write(pointer,1,rec.get('name'))
            sheet.write(pointer,2,rec.get('quantity'))
       
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
            'res_model': 'product.avaibility',
            'res_id': self.id,
        })
        return attachment
    
    def send_email_with_attachment(self, attachment,submint):
        mail = self.env['mail.mail'].create({
            'subject': submint,
            'body_html': '<p>Envio de excel adjunto con los productos minimos.</p>',
            'email_from': self.env.user.company_id.email,
            'email_to': self.env['ir.config_parameter'].sudo().get_param('email_product_min', ''),
            'attachment_ids': [(6, 0, [attachment.id])]
        })
        mail.send()