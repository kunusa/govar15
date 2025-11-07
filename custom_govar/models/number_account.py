# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo import exceptions


class numberAccount(models.Model):
    _name = 'number.account'
    
    account_id = fields.Many2one(comodel_name='account.account', string='Código agrupador',index=True)
    sales = fields.Boolean(string='Ventas')
    buys = fields.Boolean(string='Compras')