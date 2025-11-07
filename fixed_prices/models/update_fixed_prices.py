# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import xmltodict, os , tempfile, base64
from odoo import exceptions
import csv
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.misc import formatLang
import odoo.addons.decimal_precision as dp
from datetime import datetime
import io
import csv
class updateFixedPrices(models.TransientModel):
    _name = 'update.fixed.prices'

    ufp_category = fields.Many2many(comodel_name='product.category', string='Categorias')
    ufp_product_id = fields.Many2many(comodel_name='product.template',string='Producto')
    ufp_lista_1 = fields.Integer(string="lista", default="1")
    ufp_lista_2 = fields.Integer(string="lista", default="2")
    ufp_lista_3 = fields.Integer(string="lista", default="3")
    ufp_lista_5 = fields.Integer(string="lista", default="5")
    ufp_percentage_1 = fields.Integer(string="Porcentaje", required=True)
    ufp_percentage_2 = fields.Integer(string="Porcentaje", required=True)
    ufp_percentage_3 = fields.Integer(string="Porcentaje", required=True)
    ufp_percentage_5 = fields.Integer(string="Porcentaje", required=True)
    utp_bandera = fields.Boolean(string="Por producto")
    ufp_archivo = fields.Binary(string="Buscar archivo")
    ufp_productos=fields.Text(string="Productos")
    ufp_currency_fixed_id=fields.Many2one(comodel_name='res.currency', string='Moneda de Costo')

    def actualize_standard_price(self):
        for line in self:
            if line.utp_bandera == False:
                self.ufp_category
                for categoria in line.ufp_category:
                    # Categorias
                    query= f"""select * from product_template where  categ_id = {categoria.id}"""
                    self.env.cr.execute(query)
                    for p in self.env.cr.dictfetchall():
                        if line.ufp_percentage_1 > 0:
                            query1 = f"""update fixed_prices set margin_pctg = {line.ufp_percentage_1 } where product_id = {p['id'] } and list_num = { line.ufp_lista_1}"""
                            self.env.cr.execute(query1)
                        if line.ufp_percentage_2 > 0:
                            query2 = f"""update fixed_prices set margin_pctg = {line.ufp_percentage_2 } where product_id = {p['id'] } and list_num = {line.ufp_lista_2 }"""
                            self.env.cr.execute(query2)
                        if line.ufp_percentage_3 > 0:
                            query3 = f"""update fixed_prices set margin_pctg = {line.ufp_percentage_3 } where product_id = {p['id'] } and list_num = {line.ufp_lista_3 }"""
                            self.env.cr.execute(query3)
                        if line.ufp_percentage_5 > 0:
                            query5 = f"""update fixed_prices set margin_pctg = {line.ufp_percentage_5 } where product_id = {p['id'] } and list_num = {line.ufp_lista_5 }"""
                            self.env.cr.execute(query5)
            else:
                for productos in line.ufp_product_id:
                    # Productos
                    if line.ufp_percentage_1 > 0:
                        query1= f"""update fixed_prices set margin_pctg = {line.ufp_percentage_1} where product_id = {productos.id} and list_num = {line.ufp_lista_1}"""
                        self.env.cr.execute(query1)
                    if line.ufp_percentage_2 > 0:
                        query2= f"""update fixed_prices set margin_pctg = {line.ufp_percentage_2} where product_id = {productos.id} and list_num = {line.ufp_lista_2}"""
                        self.env.cr.execute(query2)
                    if line.ufp_percentage_3 > 0:
                        query3= f"""update fixed_prices set margin_pctg = {line.ufp_percentage_3} where product_id = {productos.id} and list_num = {line.ufp_lista_3}"""
                        self.env.cr.execute(query3)
                    if line.ufp_percentage_5 > 0:
                        query5= f"""update fixed_prices set margin_pctg = {line.ufp_percentage_5} where product_id = {productos.id} and list_num = {line.ufp_lista_5}"""
                        self.env.cr.execute(query5)


    def actualize_price(self):

        for line in self:
            productos_lis=""
            archivo = base64.b64decode(line.ufp_archivo)
            try:
                # Intentar con UTF-8
                archivo_texto = archivo.decode('utf-8')
            except UnicodeDecodeError:
                # Si falla, intentar con latin-1
                archivo_texto = archivo.decode('latin-1')

            filelike = io.StringIO(archivo_texto)
            csv_reader = csv.reader(filelike)
            headers = next(csv_reader)

            for i, row in enumerate(csv_reader):
                product = self.env['product.template'].search([('default_code', '=', row[1])], limit=1)
                if product:
                    product.write({'standard_price': row[2],
                                    'list_price': row[2],
                        })
                else:
                    productos_lis+="Producto:'{}', Referencia interna: '{}' \n ".format(str(row[0]), row[1])
            line.ufp_productos=productos_lis
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': self._context,
            }


    def actualize_currency_fixed(self):
        for line in self:
            for categoria in line.ufp_category:
                query="""update product_template set currency_fixed_id = { } where categ_id = { }""" % (line.ufp_currency_fixed_id.id , categoria.id)
                self.env.cr.execute(query)