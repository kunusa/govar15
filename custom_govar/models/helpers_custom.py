# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError
from datetime import datetime
import pytz

class HelpersCustom(models.AbstractModel):
    _name = 'custom.helpers'


    def table_directions_label(self,company):

        html_td = ""
        tabI = '''<table style="width:100%; font-size:15px;">'''

        tabF = '''</table>'''
        tr = '''<tr style="width:100%;">''' 
        tr2 = '''</tr>'''

        td = '''<td align="center">''' 
        td2 = '''<td/>'''        

        html_td += tabI
        if company.directions_line_id:
            html_td += tr
            for direction in company.directions_line_id:
                html_td += td
                html_td += u'''<b><span>{}<span/></b><br/>'''.format(direction.name)
                html_td += u'''<span>{}<span/> <span>{}<span/> <br/>'''.format(direction.street,direction.number)
                html_td += u'''<span>{}<span/> <span>{}<span/>, <span>{}<span/> <br/>'''.format(direction.zip,direction.city,direction.state)
                html_td += u'''<span>{}<span/><br/>'''.format(direction.phone)
                html_td += u'''<span>{}<span/><br/>'''.format(direction.email)
                html_td += td2

            html_td += tr2
            html_td += tabF

            return html_td  

    def capitalize_laters(self, word):
        string_div = word.split() if word else ''
        uper_word = [palabra.capitalize() for palabra in string_div]
        result = " ".join(uper_word)
        return  result

    def get_direction_custom(self,partner):
        country = ""
        street = ""
        city = ""
        num_int = ""
        num_ext = ""
        col = ""

        if partner.street:
            street =  partner.street
        if partner.country_id:
            country = partner.country_id.name
        if partner.city:
            city = partner.city
        if partner.numero_ext:
            num_ext = f"No. {partner.numero_ext}"
        if partner.numero_int:
            num_int = f"Ext. {partner.numero_int}"
        if partner.colonia:
            col = f"Col. {partner.colonia}"

        direction = f"{partner.name} {street} {num_ext} {num_int} {col} {city} {partner.state_id.code} {country} {partner.zip}"
        direction = direction.lower()
        return self.capitalize_laters(direction)

    def get_day_time_custom(self):

        current_time_utc = datetime.now(pytz.utc)
        mazatlan_timezone = pytz.timezone('America/Mazatlan')
        current_time_mazatlan = current_time_utc.astimezone(mazatlan_timezone)

        return current_time_mazatlan.strftime('%d-%m-%Y %H:%M:%S')

    def send_email_cp(self, template, subject, email_to, email_from, record_id, model, attachment=None):
        """
        Envía un correo electrónico usando un template de Odoo 15
        """
        import ipdb; ipdb.set_trace()
        self.env['mail.template'].browse(self.env.ref(template).id).send_mail(
            record_id,  # ID del registro relacionado
            force_send=True,
            email_values={
                'email_from': email_from,  # Quién envía
                'email_to': email_to,     # Quién recibe
                'subject': subject,  # Título/Asunto
            }
            )

    def get_url_folio(self,modelo,action,id): 
        url = ""
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = "{}/web#id={}&view_type=form&model={}&action={}".format(base_url,id,modelo,action)
        return url
