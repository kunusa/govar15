from odoo import api, fields, models, _
from odoo.exceptions import UserError


class accountMoveInherit(models.Model):
    _inherit = 'account.move'

    def delete_lines(self):
        """Enfocarse en la factura en lugar de las líneas individuales"""
        for invoice in self:
            lines_to_delete = invoice.invoice_line_ids.filtered(lambda l: l.line_delete)
            
            if not lines_to_delete:
                continue
                            
            # Crear nueva lista de líneas sin las marcadas para eliminar
            new_line_vals = []
            for line in invoice.invoice_line_ids:
                if line not in lines_to_delete:
                    new_line_vals.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'quantity': line.quantity,
                        'price_unit': line.price_unit,
                        'account_id': line.account_id.id,
                        'tax_ids': [(6, 0, line.tax_ids.ids)],
                    }))
            
            # Reemplazar todas las líneas
            invoice.write({
                'invoice_line_ids': [(5, 0, 0)] + new_line_vals
            })
            
            # Recomputar totales
            # invoice._recompute_lines()
        
        # return True

        # import ipdb; ipdb.set_trace()
        # for move in lines_to_delete.mapped('move_id'):
        #     if move.state == 'posted':
        #         # Si está publicado, cancelar y recrear
        #         move.button_draft()  # Poner en borrador
            
        #     # Obtener todas las líneas que se mantienen
        #     lines_to_keep = move.line_ids - lines_to_delete
            
        #     if not lines_to_keep:
        #         raise UserError(_("No se puede eliminar todas las líneas del asiento"))
            
        #     # Eliminar todas las líneas del asiento
        #     move.line_ids.unlink()
            
        #     # Recrear solo las líneas que se mantienen
        #     # for line in lines_to_keep:
        #     #     line.copy({'move_id': move.id})
            
        #     # Validar el asiento
        #     move._check_balanced()
        
        # return True

    

class accountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    line_delete = fields.Boolean(string=' ', default=False, store=True)


