from odoo import fields, models

class ResCompanyInherit(models.Model):
    _inherit = 'res.company'

    colonia = fields.Char(string='Colonia', placeholder='Colonia')
    numero_int = fields.Char(string='Numero Int', placeholder='Numero Int')
    numero_ext = fields.Char(string='Numero Exterior', placeholder='Numero Exterior')
    rfc_to_send = fields.Char(string = 'Rfc para envio')
    slogan = fields.Char(string='Slogan')
    message_stock = fields.Boolean('Mensaje stock')
    banks_line_id =fields.One2many(comodel_name='banks.company',inverse_name='id_bank',index=True)

class res_company_field(models.Model):
	_name = 'banks.company'

	name = fields.Char(string = 'Nombre')
	account = fields.Char(string = 'Cuenta')
	clabe = fields.Char(string = 'Clabe interbancaria')
	id_bank = fields.Many2one(inverse_name='banks_line_id',comodel_name="res.company", string="Bancos",invisible=True)
	secuence = fields.Integer(string = 'Secuencia')
    