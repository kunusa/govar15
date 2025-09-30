# -*- coding: utf-8 -*-


from odoo import api, models, fields, _
from odoo import exceptions
from datetime import datetime, date
import base64

try:
	import xlsxwriter
except ImportError:
	_logger.warning("Cannot import xlsxwriter")
	xlsxwriter = False

class saleOrderCheckInventory(models.Model):
    _inherit ='sale.order'
	

    def action_confirm(self):
        warning = {}
        title = False
        message = False
        partner = self.partner_id		

        # self.validate_price()
        if partner.sale_warn != 'no-message':
            title = ("Warning for %s") % partner.name
            message = partner.sale_warn_msg
            warning = {
                    'title': title,
                    'message': message,
            }
            if partner.sale_warn == 'block':
                raise exceptions.UserError(_('ClIENTE BLOQUEADO \n {} ').format(message))	

        # Llamar al método original usando super()
        result = super().action_confirm()
        
        # Ejecutar la lógica adicional después del método original
        self.check_inventory()
        
        return result


    def check_inventory(self):
        products = []
        for rec in self.order_line:
            qty = 0
            warehouse_obj = self.env['stock.warehouse']
            warehouse_list = warehouse_obj.search([('view_on_sale', '=', True)])
            for warehouse in warehouse_list:
                # En Odoo 15, usar free_qty en lugar de immediately_usable_qty
                available_qty = rec.product_id.with_context({'warehouse': warehouse.id}).free_qty
                qty += available_qty
            if qty <= 3 and rec.product_id.product_tmpl_id.type == 'product':
                products.append(rec.product_id)

        if products:
            self.create_and_send_excel(products)

    def generate_report(self, products):


        date_today = date.today()
        date_today = date_today.strftime("%d/%m/%Y")

        # crear libro de trabajo con hoja de trabajo

        book = xlsxwriter.Workbook('/tmp/sample.xlsx')
        sheet = book.add_worksheet('Inventario 0')

        submint = f"Alerta de productos 3 o menor {self.env.cr.dbname} {date_today}"

        #Primer periodo
        sheet.write(1,0,'Codigo')
        sheet.write(1,1,'Producto')

        sheet.set_column('A:A', 160/7)
        sheet.set_column('B:B', 250/7)

        pointer = 1
        #Generar titulos 

        sheet.merge_range('A1:E1',submint)


        for product in products:

            pointer += 1
            sheet.write(pointer,0,product.default_code)
            sheet.write(pointer,1,product.product_tmpl_id.name)

        pointer = 1

        book.close()

        return '/tmp/sample.xlsx',submint



    def create_and_send_excel(self,products):
        # Crear el archivo Excel

        file_path,submint = self.generate_report(products)

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
            'res_model': 'sale.order',
            'res_id': self.id,
        })

        return attachment
	
    def send_email_with_attachment(self, attachment,submint):
        mail = self.env['mail.mail'].create({
            'subject': submint,
            'body_html': f"<p>Alerta de producto de '{self.env.cr.dbname}'.</p>",
            'email_from': self.env.user.company_id.email,
            'email_to': self.env['ir.config_parameter'].sudo().get_param('email_product_min_3', ''),
            'attachment_ids': [(6, 0, [attachment.id])]
        })
        mail.send()

class StockConfig(models.TransientModel):

    """Add options to easily install the submodules"""
    _inherit = 'res.config.settings'

    email_product_min = fields.Char(string='Envio de correo')
    email_product_min_3 = fields.Char(string='Envio de correo')

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('email_product_min', self.email_product_min or '')
        self.env['ir.config_parameter'].sudo().set_param('email_product_min_3', self.email_product_min_3 or '')
    
    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            email_product_min=self.env['ir.config_parameter'].sudo().get_param('email_product_min', ''),
            email_product_min_3=self.env['ir.config_parameter'].sudo().get_param('email_product_min_3', ''),
        )
        return res


