from odoo.exceptions import UserError
from odoo import api, fields, models
import base64

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_message_post(self, message):
        display_msg = f"""
                        <p> El cliente ha sido {message} por {self.write_uid.partner_id.name} </p>
                    
                    """
        return display_msg

    def write(self, vals):

        res = super().write(vals)
        if  self.create_date == self.write_date:
            return res
        else:
            # context = self._context
            # if context.get('params'):
                # if self._context['params']['action'] in [55,56,57]:
                #     if not self.user_has_groups('ventas_govar.permission_crete_vendors') and self.supplier:
                #         raise UserError('No cuenta con el permiso para modificar un proveedor')
                #     if not self.user_has_groups('ventas_govar.visualize_crete_client') and self.customer:
                #         raise UserError('No cuenta con el permiso para modificar un cliente') 

                #Envio de correo cuando se modifica un cliente/proveedor
                # if self.customer and not vals.get('sale_warn'):
                #     self.send_email_cp('ventas_govar.write_client_email_template','Modificación de cliente',self.env['ir.values'].get_default('account.config.settings','email_users'),self.write_uid.login,self.id,'res.partner',None)
                # elif self.supplier:
                #     self.send_email_cp('ventas_govar.write_supplier_email_template','Modificación de proveedor',self.env['ir.values'].get_default('account.config.settings','email_users'),self.write_uid.login,self.id,'res.partner',None)
            
            #Envio de correo cuando de bloquea/debloquea un cliente
            if vals.get('sale_warn') in ['no-message','warning'] or vals.get('sale_warn') == False:
                display_msg = self.get_message_post('desbloqueado')
                self.message_post(body=display_msg)
                email_block = self.env['ir.config_parameter'].sudo().get_param('email_block', '')
                self.env['custom.helpers'].send_email_cp('custom_govar.unblock_email_template','Cliente desbloqueado',email_block,self.write_uid.login,self.id,'res.partner',None)
            if vals.get('sale_warn') == 'block':
                display_msg = self.get_message_post('bloqueado')
                self.message_post(body=display_msg)
                email_block = self.env['ir.config_parameter'].sudo().get_param('email_block', '')
                self.env['custom.helpers'].send_email_cp('custom_govar.block_email_template','Cliente bloqueado',email_block,self.write_uid.login,self.id,'res.partner',None)
        return res

    def get_url_folio(self):
        return self.env['custom.helpers'].get_url_folio('res.partner',self._context['params']['action'],self.id)

    def send_account_state(self):

        pdf_content, content_type = self.env['report.report_overdue'].render_html([self.id],self)



        attatchment_state = self.env['ir.attachment'].sudo().create({
                                'name': 'Pagos_pendientes.pdf',
                                'datas': base64.b64encode(pdf_content).decode('utf-8'),
                                'res_model': self._name
        })

        # Obtener emails de notificación del campo partner_notifica_ids
        notification_emails = [self.email]
        if self.partner_notifica_ids:
            for partner in self.partner_notifica_ids:
                if partner.correo:
                    notification_emails.append(partner.correo)
        email_to = ",".join(notification_emails)

        if email_to:
            self.env['custom.helpers'].send_email_cp(
                'custom_govar.pending_payment_template',
                'Pagos pendientes',
                email_to,
                self.env.user.login,
                self.id,
                'res.partner',
                attatchment_state
            )