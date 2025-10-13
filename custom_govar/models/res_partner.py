from odoo.exceptions import UserError
from odoo import api, fields, models
from datetime import datetime, date
import base64

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_note_count = fields.Integer(string='Notas de Crédito', compute='_compute_credit_note_count')
    cancelled_invoice_count = fields.Integer(string='Facturas Canceladas', compute='_compute_cancelled_invoice_count')
    block_customers = fields.Html(string= 'Clientes bloqueados')


    def block_customer(self):
        import ipdb; ipdb.set_trace()
        customers = self.env['res.partner'].search([('customer_rank','>',True),('active','=',True)])
        company = self.env['res.company'].search([],limit = 1)
        date_today = datetime.today()
        date_today = date_today.date()
        diff = 0
        customer_list = [] 
        flag_customer = False

        for customer in customers:
            if len(customer.invoice_ids) >= 1:
                if customer.invoice_ids[0].invoice_date:
                    old_invoice = customer.invoice_ids[0].invoice_date

                    diff = abs((date_today - old_invoice).days)

                    if diff >= 365 and customer.sale_warn != 'block': 
                        customer.update({
                            'sale_warn': "block",
                            'sale_warn_msg': "Bloqueado por inactividad"
                        })
                        flag_customer = True
                        customer_list.append(customer)
                    if diff >= 365 and customer.sale_warn_msg == 'Bloqueado por inactividad':
                        flag_customer = True
                        customer_list.append(customer)						

        if flag_customer == True:
            customer.block_customers = self.create_list_customer(customer_list)
            self.env['custom.helpers'].send_email_cp('custom_govar.block_email_one_year_template','Clientes bloqueados',self.env['ir.config_parameter'].sudo().get_param('email_block_all', ''),company.email,customer.id,'res.partner',None)
        else:
            self.env['custom.helpers'].send_email_cp('custom_govar.block_email_one_year_non_template','Clientes bloqueados',self.env['ir.config_parameter'].sudo().get_param('email_block_all', ''),company.email,customer.id,'res.partner',None)
    def get_data_base(self):
        if self.env.cr.dbname == 'Repara':
            today = date.today()
            date_base = f"{'Repara'} {today}"
            return date_base
        
        elif self.env.cr.dbname == 'Reno':

            today = date.today()
            date_base = f"{'Reno'} {today}"
            
            return date_base	
        else:
            return ""
        		

    def create_list_customer(self,customer_list):
        html_td = ""
        html_td += '''<table style="with:100%;">'''
        table = '''</table>'''
        tr = '''<tr >''' 
        tr2 = '''</tr>'''

        for customer in customer_list:
            html_td += tr
            html_td += f'''<td >{customer.name}</td>'''
            html_td += tr2

        html_td += table
        return html_td

    @api.depends()
    def _compute_credit_note_count(self):
        """Calcula el número de notas de crédito del partner"""
        for partner in self:
            partner.credit_note_count = self.env['account.move'].search_count([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'out_refund')
            ])

    @api.depends()
    def _compute_cancelled_invoice_count(self):
        """Calcula el número de facturas canceladas del partner"""
        for partner in self:
            partner.cancelled_invoice_count = self.env['account.move'].search_count([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'cancel')
            ])

    def action_view_credit_notes(self):
        """Abre la vista de notas de crédito del partner"""
        self.ensure_one()
        action = {
            'name': 'Notas de Crédito',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id), ('move_type', '=', 'out_refund')],
            'context': {
                'default_partner_id': self.id,
                'default_move_type': 'out_refund'
            }
        }
        return action

    def action_view_cancelled_invoices(self):
        """Abre la vista de facturas canceladas del partner"""
        self.ensure_one()
        action = {
            'name': 'Facturas Canceladas',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id), ('move_type', '=', 'out_invoice'), ('state', '=', 'cancel')],
            'context': {
                'default_partner_id': self.id,
                'default_move_type': 'out_invoice'
            }
        }
        return action

    def get_message_post(self, message):
        display_msg = f"""
                        <p> El cliente ha sido {message} por {self.write_uid.partner_id.name} </p>
                    
                    """
        return display_msg

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if res.customer_rank > 0:
            self.env['custom.helpers'].send_email_cp('custom_govar.create_client_email_template','Cliente creado',self.env['ir.config_parameter'].sudo().get_param('email_users', ''),res.create_uid.login,res.id,'res.partner',None)
        elif res.supplier_rank > 0:
            self.env['custom.helpers'].send_email_cp('custom_govar.create_supplier_email_template','Proveedor creado',self.env['ir.config_parameter'].sudo().get_param('email_users', ''),res.create_uid.login,res.id,'res.partner',None)
        return res

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
            if self.customer_rank > 0 and not vals.get('sale_warn'):
                self.env['custom.helpers'].send_email_cp('custom_govar.write_client_email_template','Modificación de cliente',self.env['ir.config_parameter'].sudo().get_param('email_users', ''),self.write_uid.login,self.id,'res.partner',None)
            elif self.supplier_rank > 0:
                self.env['custom.helpers'].send_email_cp('custom_govar.write_supplier_email_template','Modificación de proveedor',self.env['ir.config_parameter'].sudo().get_param('email_users', ''),self.write_uid.login,self.id,'res.partner',None)
            
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
        # Get the action from context if available, otherwise use a default action
        action = None
        if self._context.get('params') and self._context['params'].get('action'):
            action = self._context['params']['action']
        else:
            # Try to get the default action for res.partner model
            action_record = self.env['ir.actions.act_window'].search([
                ('res_model', '=', 'res.partner'),
                ('view_mode', '=', 'form')
            ], limit=1)
            if action_record:
                action = action_record.id
            else:
                # Fallback: use a generic URL without action
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                return f"{base_url}/web#id={self.id}&view_type=form&model=res.partner"
        
        return self.env['custom.helpers'].get_url_folio('res.partner', action, self.id)

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