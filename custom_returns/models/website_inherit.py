# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class websiteInherit(models.Model):
    _inherit = 'help.ticket'


    web_main_id = fields.One2many(string="Reclamo", comodel_name='customer.claim',inverse_name='web_claim_id',track_visibility='onchange')    
    is_claim = fields.Boolean(string = 'Reclamo', default = False)
    category_claim = fields.Char(string = 'Motivo de reclamo')
    reponse_claim = fields.Char(string= 'Respuesta')
    state_claim = fields.Selection([
        ('waiting', 'En espera'),
        ('acept', 'Aceptado'),
        ('refused', 'Rechazado')
    ], string='Estado de reclamo', default= "waiting")
    folio_claim = fields.Char(string="Folio")
    mobile = fields.Char(string="Telefono")
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

        sequence=self.env['ir.sequence'].next_by_code('customer.claim')
        vals['folio_claim']=sequence
        new_id = super(websiteInherit, self).create(vals)
        
        if new_id.category.name == 'Reclamos' and not new_id.person_name:
            raise UserError('El nombre es obligatorio para la creacion del reclamo')
        
        
        #(BACK COMPATABILITY) Fail safe if no template is selected, future versions will allow disabling email by removing template
        ticket_open_email_template = self.env.ref('website_support.website_ticket_state_open').mail_template_id
        if ticket_open_email_template == False:
            ticket_open_email_template = self.env['ir.model.data'].sudo().get_object('website_support', 'support_ticket_new')
            ticket_open_email_template.send_mail(new_id.id, True)
        else:
            ticket_open_email_template.send_mail(new_id.id, True)

        #Send an email out to everyone in the category
        notification_template = self.env.ref('website_support.new_support_ticket_category') 
        support_ticket_menu = self.env.ref('website_support.website_support_ticket_menu')
        support_ticket_action = self.env.ref('website_support.website_support_ticket_action') 
        for my_user in new_id.category.cat_user_ids:
            values = notification_template.generate_email(new_id.id)
            values['body_html'] = values['body_html'].replace("_ticket_url_", "web#id=" + str(new_id.id) + "&view_type=form&model=website.support.ticket&menu_id=" + str(support_ticket_menu.id) + "&action=" + str(support_ticket_action.id) ).replace("_user_name_",  my_user.partner_id.name)
            values['body'] = values['body_html']
            values['email_to'] = my_user.partner_id.email
                        
            send_mail = self.env['mail.mail'].create(values)
            send_mail.send()
            
            #Remove the message from the chatter since this would bloat the communication history by a lot
            send_mail.mail_message_id.res_id = 0

        return new_id

# class websiteInheritCompose(models.Model):
#     _inherit = 'website.support.ticket.compose'
    
#     def send_reply(self):
#         #Send email 
#         values = {}

#         setting_staff_reply_email_template_id = self.env['ir.values'].get_default('website.support.settings', 'staff_reply_email_template_id')
        
#         if setting_staff_reply_email_template_id:
#             email_wrapper = self.env['mail.template'].browse(setting_staff_reply_email_template_id)
#         else:
#             #Defaults to staff reply template for back compatablity
#             email_wrapper = self.env['ir.model.data'].get_object('website_support','support_ticket_reply_wrapper')

#         values = email_wrapper.generate_email([self.id])[self.id]
#         values['model'] = "website.support.ticket"
#         values['res_id'] = self.ticket_id.id
#         send_mail = self.env['mail.mail'].create(values)
#         send_mail.send()
        
#         #Add to message history field for back compatablity
#         self.env['website.support.ticket.message'].create({'ticket_id': self.ticket_id.id, 'by': 'staff', 'content':self.body.replace("<p>","").replace("</p>","")})
        
#         #Post in message history
#         #self.ticket_id.message_post(body=self.body, subject=self.subject, message_type='comment', subtype='mt_comment')

#         if self.approval:
#             #Change the ticket state to awaiting approval
#             awaiting_approval_state = self.env['ir.model.data'].get_object('website_support','website_ticket_state_awaiting_approval')
#             self.ticket_id.state = awaiting_approval_state.id
        
#             #Also change the approval
#             awaiting_approval = self.env['ir.model.data'].get_object('website_support','awaiting_approval')
#             self.ticket_id.approval_id = awaiting_approval.id        
#         else:
#             #Change the ticket state to staff replied        
#             staff_replied = self.env['ir.model.data'].get_object('website_support','website_ticket_state_staff_replied')
#             self.ticket_id.state = staff_replied.id
        
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
    
    
class website_support_claim_inherit(models.TransientModel):

    _inherit = "res.config.settings"   
    
    email_claim = fields.Char(string="Email") 
    telefono_claim = fields.Char(string="Telefono") 
    email_claim_show = fields.Char(string="Sitio web email") 
      
    
    #-----EMAIL-----

    def get_default_email_claim(self, fields):
        return {'email_claim': self.env['ir.values'].get_default('website.support.settings', 'email_claim')}

    def set_default_email_claim(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'email_claim', record.email_claim)


    #-----EMAIL SITIO WEB-----

    def get_default_email_claim_show(self, fields):
        return {'email_claim_show': self.env['ir.values'].get_default('website.support.settings', 'email_claim_show')}

    def set_default_email_claim_show(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'email_claim_show', record.email_claim_show)         
            

    #-----EMAIL SITIO WEB-----

    def get_default_telefono_claim(self, fields):
        return {'telefono_claim': self.env['ir.values'].get_default('website.support.settings', 'telefono_claim')}

    def set_default_telefono_claim(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'telefono_claim', record.telefono_claim)         