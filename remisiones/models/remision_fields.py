
from odoo import api, fields, models, _


class productTemplateInherit(models.Model):
    _inherit = 'product.template'

    count_rem = fields.Integer(string='Remisiones', compute='_compute_remision_ids')
    rem_ids = fields.Many2many(comodel_name='remision_line', string= 'Remisiones')

    @api.depends('rem_ids')
    def _compute_remision_ids(self):
        for product in self:
            product.count_rem = len(product.rem_ids)

    
    def action_view_remision(self):
        action = self.env.ref('remisiones.action_remisiones_line_tree').read()[0]
        rems = self.mapped('rem_ids')
        action['domain'] = [('id', 'in', rems.ids)]

        return action

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10):

        args = args or []
        product_ids = []
        if name:            
            product_ids = self._search([('name', '=', name)] + args, limit=limit)
        if not product_ids:
            product_ids = self._search([('default_code', operator, name)] + args, limit=limit)

        return self.browse(product_ids).name_get()

class remisionesPartner(models.Model):
    _inherit = 'res.partner'

    count_rem_p = fields.Integer(string='Remisiones', compute='_compute_remision_ids')
    rem_ids = fields.Many2many(comodel_name='remision', string= 'Remisiones')
    less_price = fields.Boolean('Precio venta menor', help = "Activar opciones de limite de precio") 

    @api.depends('rem_ids')
    def _compute_remision_ids(self):
        for rec in self:
            rec.count_rem_p = len(rec.rem_ids)

    def action_view_remision_p(self):
        action = self.env.ref('remisiones.view_remisiones_button_tree').read()[0]
        rems = self.mapped('rem_ids')
        action['domain'] = [('id', 'in', rems.ids)]

        return action

class resCmpanyRemision(models.Model):
    _inherit = 'res.company'

    list_validate = fields.Boolean('Lista de precio', help = "Activa la validación de lista de precio menor a 3")
    message_rem_mot = fields.Boolean('Motivos remisión', help = "Aparece los motivos en las remisiones")
    directions_line_id =fields.One2many(comodel_name='directions.report',inverse_name='id_direction',index=True)



class directions_report(models.Model):
	_name = 'directions.report'

	id_direction = fields.Many2one(inverse_name='directions_line_id',comodel_name="res.company", string="Direccion",invisible=True)
	name = fields.Char(string = 'Nombre')
	street = fields.Char(string = 'Calle')
	number = fields.Char(string = 'Numero')
	zip = fields.Char(string = 'Codigo postal')
	city = fields.Char(string = 'Ciudad')
	state = fields.Char(string = 'Estado')
	phone = fields.Char(string = 'Telefono')
	email = fields.Char(string = 'Correo')