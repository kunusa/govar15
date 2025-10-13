
from odoo import api, fields, models, _



class customerBlockWizard(models.TransientModel):

    _name = 'customer.block'


    def block_customers(self):
        
        res_object = self.env['res.partner']

        res_object.block_customer()