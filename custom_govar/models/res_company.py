from odoo import fields, models

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    colonia = fields.Char(string='Colonia', placeholder='Colonia')
    numero_int = fields.Char(string='Numero Int', placeholder='Numero Int')
    numero_ext = fields.Char(string='Numero Exterior', placeholder='Numero Exterior')
    rfc_to_send = fields.Char(string = 'Rfc para envio')
    slogan = fields.Char(string='Slogan')
    message_stock = fields.Boolean('Mensaje stock')