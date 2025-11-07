from odoo import fields, models, api

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'
    
    list_validate = fields.Boolean('Lista de precio', help = "Activa la validación de lista de precio menor a 3")

class ResPartner(models.Model):
    _inherit = 'res.partner'

    list_num = fields.Integer(string='Lista',index=True)
    less_price = fields.Boolean('Precio venta menor', help = "Activar opciones de limite de precio") 

class saleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    price_list = fields.Integer(string="Lista")

    @api.onchange('price_list')
    def _onchange_listprice(self):

        for rec in self:
            if not rec.product_id.product_tmpl_id.id == False:
                list_search = self.env['fixed.prices'].sudo().search([('list_num','=',rec.price_list),('product_id','=',rec.product_id.product_tmpl_id.id)])
                if not list_search:
                    rec.price_list= 1
                elif rec.product_id.currency_fixed_id.id != self.company_id.currency_id.id:
                    rec.price_unit = list_search.price * rec.order_id.currency_id.rate 
                else:
                    rec.price_unit = list_search.price

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):

        self.price_list = self.order_id.partner_id.list_num or 1
        if not self.product_uom:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            # product = self.product_id.with_context(
            #     lang=self.order_id.partner_id.lang,
            #     partner=self.order_id.partner_id.id,
            #     quantity=self.product_uom_qty,
            #     date_order=self.order_id.date_order,
            #     pricelist=self.order_id.pricelist_id.id,
            #     uom=self.product_uom.id,
            #     fiscal_position=self.env.context.get('fiscal_position')
            # )

            self.price_unit = self.env['fixed.prices'].sudo().search([('list_num','=',self.price_list),('product_id','=',self.product_id.product_tmpl_id.id)]).price