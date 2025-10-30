# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class WebsiteSupportTicket(models.Model):
    _inherit = 'website.support.ticket'

    web_main_id = fields.One2many(string="Reclamo", comodel_name='customer.claim', inverse_name='web_claim_id', tracking=True)    
    is_claim = fields.Boolean(string='Reclamo', default=False)
    category_claim = fields.Char(string='Motivo de reclamo')
    reponse_claim = fields.Char(string='Respuesta')
    state_claim = fields.Selection([
        ('waiting', 'En espera'),
        ('acept', 'Aceptado'),
        ('refused', 'Rechazado')
    ], string='Estado de reclamo', default="waiting", tracking=True)
    folio_claim = fields.Char(string="Folio", readonly=True)
    mobile = fields.Char(string="Teléfono")
    phone = fields.Char(string="WhatsApp")
    contact = fields.Char(string="Contacto")
    agent = fields.Char(string="Comercial")

    def attend_claim(self):

        context = dict(self._context or {})
        context.update({'ticket_id': self.id})
        
        return {
            'name': 'Reclamo',
            'type': 'ir.actions.act_window',
            'res_model': 'claim.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context
        }

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('customer.claim')
        vals['folio_claim'] = sequence
        new_id = super(WebsiteSupportTicket, self).create(vals)
        
        if new_id.category_id.name == 'Reclamos' and not new_id.person_name:
            raise UserError('El nombre es obligatorio para la creación del reclamo')
        
        # Send email notification using Odoo 15 API
        ticket_open_email_template = self.env.ref('website_support.website_ticket_state_open').mail_template_id
        if not ticket_open_email_template:
            ticket_open_email_template = self.env.ref('website_support.support_ticket_new')
            ticket_open_email_template.send_mail(new_id.id, force_send=True)
        else:
            ticket_open_email_template.send_mail(new_id.id, force_send=True)

        # Send notification to category users
        notification_template = self.env.ref('website_support.new_support_ticket_category') 
        support_ticket_menu = self.env.ref('website_support.website_support_ticket_menu')
        support_ticket_action = self.env.ref('website_support.website_support_ticket_action') 
        
        for my_user in new_id.category_id.cat_user_ids:
            fields_to_generate = ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date']
            values = notification_template.generate_email([new_id.id], fields=fields_to_generate)
            if new_id.id in values:
                values = values[new_id.id]
            values['body_html'] = values['body_html'].replace("_ticket_url_", "web#id=" + str(new_id.id) + "&view_type=form&model=website.support.ticket&menu_id=" + str(support_ticket_menu.id) + "&action=" + str(support_ticket_action.id)).replace("_user_name_", my_user.partner_id.name)
            values['body'] = values['body_html']
            values['email_to'] = my_user.partner_id.email
                        
            send_mail = self.env['mail.mail'].create(values)
            send_mail.send()
            
            # Remove the message from the chatter since this would bloat the communication history by a lot
            if send_mail.mail_message_id:
                send_mail.mail_message_id.res_id = 0

        return new_id
        
class ClaimWizard(models.TransientModel):
    _name = 'claim.wizard'
    _description = 'Wizard para abrir facturas'

    note_claim = fields.Char(string="Razon")

    def accept_claim(self):
        tickt_id = self.env['website.support.ticket'].search([('id','=',self._context.get('ticket_id'))])
        tickt_id.state_claim = 'acept'
        tickt_id.reponse_claim = self.note_claim

        
    def denied_claim(self):
        tickt_id = self.env['website.support.ticket'].search([('id','=',self._context.get('ticket_id'))])
        tickt_id.state_claim = 'refused'
        tickt_id.reponse_claim = self.note_claim
    
    
class WebsiteSupportClaimSettings(models.TransientModel):
    _inherit = "res.config.settings"   
    
    email_claim = fields.Char(string="Email") 
    telefono_claim = fields.Char(string="Teléfono") 
    email_claim_show = fields.Char(string="Sitio web email") 
      
    def set_values(self):
        super(WebsiteSupportClaimSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('custom_returns.email_claim', self.email_claim)
        self.env['ir.config_parameter'].sudo().set_param('custom_returns.telefono_claim', self.telefono_claim)
        self.env['ir.config_parameter'].sudo().set_param('custom_returns.email_claim_show', self.email_claim_show)

    def get_values(self):
        res = super(WebsiteSupportClaimSettings, self).get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res.update(
            email_claim=ICP.get_param('custom_returns.email_claim', ''),
            telefono_claim=ICP.get_param('custom_returns.telefono_claim', ''),
            email_claim_show=ICP.get_param('custom_returns.email_claim_show', '')
        )
        return res         