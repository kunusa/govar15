# -*- coding: utf-8 -*-
from odoo import models, api, fields, _

TYPE_ACCOUNT = [
        ('discount_sale', 'Descuento sobre venta'),
        ('refaund_sale','Devolución sobre venta '),
        ('discount_purchase', 'Descuento sobre compra'),
        ('refaund_purchase','Devolución sobre compra ')
]


class AccountInvoiceRefund(models.TransientModel):
    """Refunds invoice"""

    _inherit = "account.move.reversal"
    
    type_account = fields.Selection(
        selection=TYPE_ACCOUNT,
        string='Tipo de nota de crédito')
    reference = fields.Char(string = 'Referencia')

    
    def reverse_moves(self):
        # Crear contexto con type_account y reference
        context = self.env.context.copy()
        if self.type_account:
            context.update({
                'type_account': self.type_account,
                'reference': self.reference or ''
            })
        
        # Llamar al método padre con el contexto actualizado
        res = super(AccountInvoiceRefund, self.with_context(context)).reverse_moves()
        
        return res
