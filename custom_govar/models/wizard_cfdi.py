# -*- coding: utf-8 -*-
from odoo import models, api, fields
from io import BytesIO
import base64
import zipfile

class cfdiIssue(models.TransientModel):
    _name = 'cfdi.issue'


    initial_date = fields.Date(string = 'Fecha Inicial')
    final_date = fields.Date(string = 'Fecha final')
    partner_id = fields.Many2one('res.partner', string = 'Cliente',domain = [('customer_rank', '>', 0)])
    is_cfdi = fields.Boolean(string = 'XML', default = True)
    is_pdf = fields.Boolean(string = 'PDF', default = False)
    
    
    def download_cfdi(self):

        if self.partner_id:
            invoices = self.env['account.move'].search([
                ('invoice_date', '>=', self.initial_date),
                ('invoice_date', '<=', self.final_date),
                ('state', '=', 'posted'),
                ('partner_id', '=', self.partner_id.id),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ])
        else:
            invoices = self.env['account.move'].search([
                ('invoice_date', '>=', self.initial_date),
                ('invoice_date', '<=', self.final_date),
                ('state', '=', 'posted'),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ])
                
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for invoice in invoices:
                if self.is_cfdi:
                    attachments = self.env['ir.attachment'].search([
                        ('res_model', '=', 'account.move'),
                        ('res_id', '=', invoice.id),
                        ('mimetype', '=', 'application/xml')
                    ], limit = 1)
                    if attachments.datas:
                        for attachment in attachments:
                            zip_file.writestr(attachment.name, base64.b64decode(attachment.datas))
                if self.is_pdf:
                    attachments = self.env['ir.attachment'].search([
                        ('res_model', '=', 'account.move'),
                        ('res_id', '=', invoice.id),
                        ('mimetype', '=', 'application/pdf')
                    ], limit = 1)
                    if attachments.datas:
                        for attachment in attachments:
                            zip_file.writestr(attachment.name, base64.b64decode(attachment.datas))
        zip_buffer.seek(0)
        zip_data = base64.b64encode(zip_buffer.read())
        zip_buffer.close()
        
        attachment = self.env['ir.attachment'].create({
            'name': 'CFDI Emitidos.zip',
            'datas': zip_data,
            'type': 'binary',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }