from odoo import api, fields, models, _
from odoo import exceptions


class accountMoveInherit(models.Model):
    _inherit = 'account.move'


    def action_post(self):
        """
        Hereda el método action_post y agrega el envío de correo
        """
        # Llamar al método original
        result = super().action_post()
        # Enviar correo después de confirmar la factura
        self.send_email_company()
        
        return result

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
            
    def send_email_company(self):
        """
        Envía correo cuando se crea una factura para la empresa
        """
        # Obtener el correo de configuración
        email_company = self.env['ir.config_parameter'].sudo().get_param('email_company', '')
        
        if not email_company:
            return False
            
        # Verificar si es factura de cliente y el RFC coincide
        if self.move_type == 'out_invoice' and self.partner_id.vat == self.company_id.rfc_to_send:
            subject = f'Factura creada para {self.partner_id.name}'
            self.env['custom.helpers'].send_email_cp(
                'custom_govar.create_invoice_customer_company_email_move',
                subject,
                email_company,
                self.company_id.email,
                self.id,
                'account.move',
                None
            )
        # Verificar si es factura de proveedor y el RFC coincide
        elif self.move_type == 'in_invoice' and self.partner_id.vat == self.company_id.rfc_to_send:
            subject = f'Factura creada para {self.partner_id.name}'
            self.env['custom.helpers'].send_email_cp(
                'custom_govar.create_invoice_supplier_company_email_template',
                subject,
                email_company,
                self.company_id.email,
                self.id,
                'account.move',
                None
            )

    def get_url_folio(self):
        """
        Obtiene la URL del folio de la factura
        """
        try:
            # Intentar obtener la acción del contexto web
            action_id = self._context.get('params', {}).get('action')
            if action_id:
                return self.env['custom.helpers'].get_url_folio('account.move', action_id, self.id)
        except (KeyError, AttributeError):
            pass
        
        # Si no hay contexto web, generar URL directa
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web#id={self.id}&model=account.move&view_type=form"

    @api.model
    def create(self, vals):
        type_account = self._context.get('type_account')
        res = super().create(vals)

        if res.move_type == 'out_refund' or res.move_type == 'in_refund':

            if vals.get('move_type') == "out_refund":
                if type_account in ['discount_purchase','refaund_purchase']:
                    raise exceptions.UserError("No se puede generar una nota de crédito con una cuenta de compras")
                
                # Obtener cuentas configuradas para ventas
                if type_account == 'discount_sale':
                    account_id = self.env['ir.config_parameter'].sudo().get_param('discount_sale_account', '')
                elif type_account == 'refaund_sale':
                    account_id = self.env['ir.config_parameter'].sudo().get_param('refaund_sale_account', '')
                else:
                    account_id = False
                
            if vals.get('move_type') == "in_refund":
                if type_account in ['discount_sale','refaund_sale']:
                    raise exceptions.UserError("No se puede generar una nota de crédito con una cuenta de ventas")
                
                # Obtener cuentas configuradas para compras
                if type_account == 'discount_purchase':
                    account_id = self.env['ir.config_parameter'].sudo().get_param('discount_purchase_account', '')
                elif type_account == 'refaund_purchase':
                    account_id = self.env['ir.config_parameter'].sudo().get_param('refaund_purchase_account', '')
                else:
                    account_id = False
                
            # Aplicar la cuenta a las líneas si está configurada
            if account_id:
                self._apply_account_to_lines(res, account_id)
                    
        return res
        
    def _apply_account_to_lines(self, move, account_id):
        """
        Aplica la cuenta especificada a todas las líneas de la factura
        """
        import  ipdb; ipdb.set_trace()
        id_credit = self.env['account.account'].search([('id','=',int(account_id))], limit = 1)
        try:
            for line in move.invoice_line_ids:
                line.account_id = id_credit.id
        except Exception as e:
            # Log del error pero no interrumpir el proceso
            pass

class accountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    line_delete = fields.Boolean(string=' ', default=False, store=True)


