# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import requests
from odoo.http import request
import odoo

from odoo import api, fields, models

class WebsiteSupportSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    close_ticket_email_template_id = fields.Many2one('mail.template', domain="[('model_id','=','website.support.ticket')]", string="(OBSOLETE)Close Ticket Email Template")
    change_user_email_template_id = fields.Many2one('mail.template', domain="[('model_id','=','website.support.ticket')]", string="Change User Email Template")
    staff_reply_email_template_id = fields.Many2one('mail.template', domain="[('model_id','=','website.support.ticket.compose')]", string="Staff Reply Email Template")
    email_default_category_id = fields.Many2one('website.support.ticket.category', string="Email Default Category")
    max_ticket_attachments = fields.Integer(string="Max Ticket Attachments")
    max_ticket_attachment_filesize = fields.Integer(string="Max Ticket Attachment Filesize (KB)")
    allow_user_signup = fields.Boolean(string="Allow User Signup")
    auto_send_survey = fields.Boolean(string="Auto Send Survey")
    business_hours_id = fields.Many2one('resource.calendar', string="Business Hours")
    google_recaptcha_active = fields.Boolean(string="Google reCAPTCHA Active")
    google_captcha_client_key = fields.Char(string="reCAPTCHA Client Key")
    google_captcha_secret_key = fields.Char(string="reCAPTCHA Secret Key")
    allow_website_priority_set = fields.Selection([("partner","Partner Only"), ("everyone","Everyone")], string="Allow Website Priority Set", help="Cusomters can set the priority of a ticket when submitting via the website form\nPartner Only = logged in user")


    def set_values(self):
        super(WebsiteSupportSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('website_support.auto_send_survey', self.auto_send_survey)
        self.env['ir.config_parameter'].sudo().set_param('website_support.allow_user_signup', self.allow_user_signup)
        self.env['ir.config_parameter'].sudo().set_param('website_support.change_user_email_template_id', self.change_user_email_template_id.id)
        self.env['ir.config_parameter'].sudo().set_param('website_support.close_ticket_email_template_id', self.close_ticket_email_template_id.id)
        self.env['ir.config_parameter'].sudo().set_param('website_support.email_default_category_id', self.email_default_category_id.id)
        self.env['ir.config_parameter'].sudo().set_param('website_support.staff_reply_email_template_id', self.staff_reply_email_template_id.id)
        self.env['ir.config_parameter'].sudo().set_param('website_support.max_ticket_attachments', self.max_ticket_attachments)
        self.env['ir.config_parameter'].sudo().set_param('website_support.max_ticket_attachment_filesize', self.max_ticket_attachment_filesize)
        self.env['ir.config_parameter'].sudo().set_param('website_support.business_hours_id', self.business_hours_id.id)
        self.env['ir.config_parameter'].sudo().set_param('website_support.google_recaptcha_active', self.google_recaptcha_active)
        self.env['ir.config_parameter'].sudo().set_param('website_support.google_captcha_client_key', self.google_captcha_client_key)
        self.env['ir.config_parameter'].sudo().set_param('website_support.google_captcha_secret_key', self.google_captcha_secret_key)
        self.env['ir.config_parameter'].sudo().set_param('website_support.allow_website_priority_set', self.allow_website_priority_set)
        

    def get_values(self):
        res = super(WebsiteSupportSettings, self).get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res.update(
            auto_send_survey=ICP.get_param('website_support.auto_send_survey', 'False') == 'True',
            allow_user_signup=ICP.get_param('website_support.allow_user_signup', 'False') == 'True',
            change_user_email_template_id=int(ICP.get_param('website_support.change_user_email_template_id', '0')) or False,
            close_ticket_email_template_id=int(ICP.get_param('website_support.close_ticket_email_template_id', '0')) or False,
            email_default_category_id=int(ICP.get_param('website_support.email_default_category_id', '0')) or False,
            staff_reply_email_template_id=int(ICP.get_param('website_support.staff_reply_email_template_id', '0')) or False,
            max_ticket_attachments=int(ICP.get_param('website_support.max_ticket_attachments', '2')),
            max_ticket_attachment_filesize=int(ICP.get_param('website_support.max_ticket_attachment_filesize', '500')),
            business_hours_id=int(ICP.get_param('website_support.business_hours_id', '0')) or False,
            google_recaptcha_active=ICP.get_param('website_support.google_recaptcha_active', 'False') == 'True',
            google_captcha_client_key=ICP.get_param('website_support.google_captcha_client_key', ''),
            google_captcha_secret_key=ICP.get_param('website_support.google_captcha_secret_key', ''),
            allow_website_priority_set=ICP.get_param('website_support.allow_website_priority_set', 'partner')
        )
        return res