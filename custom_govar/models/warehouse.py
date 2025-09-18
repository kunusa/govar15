

# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class CheckStock(models.Model):
    _inherit = 'stock.warehouse'
    
    view_on_sale = fields.Boolean(string='Ver Disponibilidad en Ventas',default="False")