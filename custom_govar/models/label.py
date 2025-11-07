# -*- coding: utf-8 -*-
from odoo import models, api, fields
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from datetime import datetime
import pytz

class labelWizard(models.TransientModel):
    _name = 'wz.label'

    
    invoice_id =fields.Many2one(comodel_name='account.move', string="Factura")
    remision_id =fields.Many2one(comodel_name='remision', string="Remisión")

    def generate_label(self):
        
        self.ensure_one()   
        if self.invoice_id:
            return {
                'type': 'ir.actions.report',
                'report_name': 'custom_govar.report_invoice_label',
                'report_type': 'qweb-pdf',
                'data': None,
                'res_ids': [self.invoice_id.id],
                'context': dict(
                    self.env.context,
                    active_model='account.move',
                    active_ids=[self.invoice_id.id],
                    active_id=self.invoice_id.id
                ),
                }
        
        elif self.remision_id:
            return {
                'type': 'ir.actions.report',
                'report_name': 'custom_govar.report_remision_label',
                'report_type': 'qweb-pdf',
                'data': None,
                'res_ids': [self.remision_id.id],
                'context': dict(
                    self.env.context,
                    active_model='remision',
                    active_ids=[self.remision_id.id],
                    active_id=self.remision_id.id
                ),
            }
        

class accountInvoiceLabel(models.Model):
    _inherit = 'account.move'



    directions_label = fields.Html(compute='_compute_form_table_label',string='Direcciones')

    def _compute_form_table_label(self):

        self.directions_label = self.env['custom.helpers'].table_directions_label(self.company_id)

    def get_currency_inv(self):
        currency = ""
        currency = "Pesos" if self.currency_id.name == "MXN" else "Dolares"

        return currency

    def get_direction(self,partner):
        return self.env['custom.helpers'].get_direction_custom(partner)

    def capitalize_laters(self, word):
        string_div = word.split() if word else ''
        uper_word = [palabra.capitalize() for palabra in string_div]
        result = " ".join(uper_word)
        return  result

    def capitalize_later(self, word):
        word = word.capitalize() if word else ''
        return  word  
    
    def get_day_time(self):

        return self.env['custom.helpers'].get_day_time_custom()



class remisiones_label(models.Model):
    _inherit = 'remision'

    directions_label = fields.Html(compute='_compute_rem_table_label',string='Direcciones')

    def get_day_time_rem(self):

        return self.env['custom.helpers'].get_day_time_custom()

    def _compute_rem_table_label(self):

        self.directions_label = self.env['custom.helpers'].table_directions_label(self.company_id)

    def get_currency_rem(self):

        currency = ""
        currency = "Pesos" if self.partner_id.property_product_pricelist.currency_id.name == "MXN" else "Dolares"

        return currency
    
    def get_direction(self,partner):
        return self.env['custom.helpers'].get_direction_custom(partner)

    def capitalize_laters(self, word):
        string_div = word.split() if word else ''
        uper_word = [palabra.capitalize() for palabra in string_div]
        result = " ".join(uper_word)   
        return  result

    def capitalize_later(self, word):
        word = word.capitalize() if word else ''
        return  word  