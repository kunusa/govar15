# -*- coding: utf-8 -*-
from odoo import models, api, _
import logging
from datetime import datetime, date
import base64

_logger = logging.getLogger(__name__)

try:
	import xlsxwriter
except ImportError:
	_logger.warning("Cannot import xlsxwriter")
	xlsxwriter = False


class accountInvoiceSendEmail(models.Model):
    _inherit = 'account.move'


    def check_invoices(self,date_from,date_to):
        

        query = """SELECT am.destination_invoice, am.invoice_date_due, am.state, am.invoice_origin, rp.name, am.invoice_date, am.cfdi_fecha_timbrado, am.email_message, am.name, aj.name as diario, ct.nombre as metodo_pago, rpn.name as comercial, am.amount_total, am.amount_residual FROM account_move am
        inner join res_partner rp on rp.id = am.partner_id
        inner join account_journal aj on aj.id = am.journal_id
        inner join catalogo_sat ct on ct.id = am.metodo_pago_id
        inner join res_users rus on rus.id = am.invoice_user_id
        inner join res_partner rpn on rpn.id = rus.partner_id
        where am.state = 'posted' and am.move_type = 'out_invoice' and am.invoice_date BETWEEN '{}' AND '{}' """.format(date_from,date_to)

        self.env.cr.execute(query)
        invoices = self.env.cr.dictfetchall()
        
        if invoices:
            self.create_and_send_excel(invoices)

    def generate_report_invoice(self, invoices):


        date_today = date.today()
        date_today = date_today.strftime("%d/%m/%Y")

        # crear libro de trabajo con hoja de trabajo

        book = xlsxwriter.Workbook('/tmp/sample.xlsx')
        sheet = book.add_worksheet('Facturas')

        submint = "Facturas pendienes de pago {} {}".format(self.env.cr.dbname,date_today)
        
        #Primer periodo
        sheet.write(1,0,'Cliente')
        sheet.write(1,1,'Fecha factura')
        sheet.write(1,2,'Fecha timbrado')
        sheet.write(1,3,'Documento enviado')
        sheet.write(1,4,'Numero')
        sheet.write(1,5,'Diario')
        sheet.write(1,6,'Metodo de pago')
        sheet.write(1,7,'Comercial')
        sheet.write(1,8,'Fecha de vencimiento')
        sheet.write(1,9,'Documento origen')
        sheet.write(1,10,'Total')
        sheet.write(1,11,'Importe adeudado')
        sheet.write(1,12,'Estado')
        sheet.write(1,13,'Destino')

        sheet.set_column('A:A', 250/7)#Cliente
        sheet.set_column('B:B', 160/7)#Fecha factura
        sheet.set_column('C:C', 160/7)#Fecha timbrado
        sheet.set_column('D:D', 250/7)#Documento enviado
        sheet.set_column('E:E', 130/7)#Numero
        sheet.set_column('F:F', 150/7)#Diario
        sheet.set_column('G:G', 200/7)#Metodo de pago
        sheet.set_column('H:H', 230/7)#Comercial
        sheet.set_column('J:J', 120/7)#Fecha de vencimiento
        sheet.set_column('I:I', 140/7)#Documento origen
        sheet.set_column('K:K', 120/7)#Total
        sheet.set_column('L:L', 120/7)#Importe adeudado
        sheet.set_column('M:M', 120/7)#Estado
        sheet.set_column('N:N', 250/7)#Destino

        pointer = 1
        #Generar titulos 

        sheet.merge_range('A1:N1',submint)


        for invoice in invoices:

            pointer += 1            
            
            if invoice.get('state') == 'posted':
                state_invoice = 'Abierto'
            else:
                state_invoice = invoice.get('state')

            sheet.write(pointer,0,invoice.get('name'))
            sheet.write(pointer,1,invoice.get('invoice_date'))
            sheet.write(pointer,2,invoice.get('cfdi_fecha_timbrado'))
            sheet.write(pointer,3,invoice.get('email_message'))
            sheet.write(pointer,4,invoice.get('name'))
            sheet.write(pointer,5,invoice.get('diario'))
            sheet.write(pointer,6,invoice.get('metodo_pago'))
            sheet.write(pointer,7,invoice.get('comercial'))
            sheet.write(pointer,8,invoice.get('invoice_date_due'))
            sheet.write(pointer,9,invoice.get('invoice_origin'))
            sheet.write(pointer,10,invoice.get('amount_total'))
            sheet.write(pointer,11,invoice.get('amount_residual'))
            sheet.write(pointer,12,state_invoice)
            sheet.write(pointer,13,invoice.get('destination_invoice'))

        pointer = 1

        book.close()

        return '/tmp/sample.xlsx',submint



    def create_and_send_excel(self,products):
        # Crear el archivo Excel

        file_path,submint = self.generate_report_invoice(products)

        # Adjuntar el archivo al registro
        attachment = self.attach_file_to_record(file_path,submint)

        # Enviar el correo electrónico con el archivo adjunto
        self.send_email_with_attachment(attachment,submint)

        return True
	

    def attach_file_to_record(self, file_path,submint):

        with open(file_path, 'rb') as file:
            file_data = file.read()


        attachment = self.env['ir.attachment'].create({
            'name': '{}.xlsx'.format(submint),
            'type': 'binary',
            'datas': base64.b64encode(file_data).decode('utf-8'),
            'res_model': 'account.move',
            'res_id': self.id,
        })

        return attachment
	
    def send_email_with_attachment(self, attachment,submint):

        email_cyc = self.env['ir.config_parameter'].sudo().get_param('email_cyc', '')
        if email_cyc:
            mail = self.env['mail.mail'].create({
                'subject': submint,
                'body_html': "<p>Facturas pendientes de pago ('{}').</p>".format(self.env.cr.dbname),
                'email_from': self.env.user.company_id.email,
                'email_to': email_cyc,
                'attachment_ids': [(6, 0, [attachment.id])]
            })
            mail.send()