# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import base64

class CustomWebsite(http.Controller):

    # Primer abrir vista para buscar factura
    @http.route('/customer_page', type='http', auth="public", website=True)
    def custom_page(self):
        return request.render('customer_returns.customer_claim_form', {})

    # Segundo paso abrir formulario de busquera
    @http.route('/search_invoice', type='http', auth='public', website=True, methods=['GET', 'POST'] ,csrf=True)
    def search_invoioce(self, **kwargs):

        invoice = kwargs.get('invoice')
        request.session['invoice_info'] = kwargs
        
        invoice_id = request.env['account.invoice'].sudo().search([('number','=',invoice)])
    
        # Redirigir al formulario de información con la factura encontrada
        if invoice_id:
            request.session['invoice_id'] = invoice_id.id

            return request.render('customer_returns.invoice_info_form', {
                'invoice': invoice_id,
                'lines': invoice_id.invoice_line_ids
            })
        else:
            # Si no se encuentra, mostrar mensaje de error en el segundo formulario
            return request.render('customer_returns.invoice_info_form', {
                'invoice': False,
            })

     # Buscar reclamo
    @http.route('/status/claim', type='http', auth='public', website=True, methods=['GET', 'POST'] ,csrf=True)
    def status_claim(self, **kwargs):

        return request.render('customer_returns.search_claim_form', {})
            
    # Buscar reclamo
    @http.route('/result/claim', type='http', auth='public', website=True, methods=['GET', 'POST'] ,csrf=True)
    def claim_search(self, **kwargs):
        

        claim = kwargs.get('claim').upper().strip()
        ticket_id = request.env['website.support.ticket'].sudo().search([('folio_claim','=',claim)])

        # Redirigir al formulario de información del reclamo
        if ticket_id:
            return request.render('customer_returns.claim_info_form', {
                'ticket': ticket_id
            })
        else:
            # Si no se encuentra, mostrar mensaje de error en el segundo formulario
            return request.render('customer_returns.claim_info_form', {
                'claim': False,
            })

    @http.route('/update_file', type='http', auth='public', website=True, csrf=True)
    def update_file_form(self, **post):



        file_claim = request.httprequest.files.get('file_claim')

        if file_claim:

            data = file_claim.read()
            name_file = file_claim.filename
            ticket_id = request.env['website.support.ticket'].sudo().search([('folio_claim','=',post.get('folio_claim'))]).id
        
            request.env['ir.attachment'].sudo().create({
                'name': name_file,
                'datas': data.encode('base64'),
                'datas_fname': name_file,
                'res_model': 'website.support.ticket',
                'res_id': ticket_id
            })            
        
            
            return request.render('customer_returns.update_file_form',{'file_state':True  })
        else:
            return request.render('customer_returns.update_file_form',{'file_state':False})
        
        
    @http.route('/submit/info', type='http', auth='public', website=True, csrf=True)
    def submit_form(self, **post):
        # Obtener los datos del formulario
        productos_seleccionados = []
        cantidad_por_producto = {}
        list_claim = []

        # Filtrar los productos seleccionados y sus cantidades
        for key, value in post.items():
            if key.startswith('productos[') and key.endswith(']'):
                productos_seleccionados.append(value)
            elif key.startswith('cantidad_'):
                producto_id = key.replace('cantidad_', '')
                cantidad_por_producto[producto_id] = value   
                
        lines_ids = {k: v for k, v in cantidad_por_producto.items() if v}
        

        for key,value in lines_ids.items():
            
            invoilce_line = request.env['account.invoice.line'].sudo().search([('id','=',key)])
            
            claim = (0,0, {
                'product_id': invoilce_line.product_id.id,
                'price_unit': invoilce_line.price_unit,
                'quantity_invoice': invoilce_line.quantity,
                'quantity': float(value),
                'invoice_id': request.session.get('invoice_id')
            })
            
            list_claim.append(claim)

        if post.get('motive') != 'otro':
            motive = post.get('motive')
        else:
            motive = post.get('otro_motivo')

        category = request.env['website.support.ticket.categories'].sudo().search([('name','=','Reclamos')]).id
        ticket_info = {
            'web_main_id': list_claim,            
            'email': post.get("email") if post.get("email") else "",
            'person_name': post.get("name") if post.get("name") else "",
            'category_claim':motive,
            'mobile': post.get("phone") if post.get("phone") else "",
            'phone': post.get("mobile") if post.get("mobile") else "",
            'contact': post.get("cotanct") if post.get("cotanct") else "",
            'agent': post.get('agent') if post.get('agent') else "",
            'is_claim': True,
            'category':category,
            'subject': "Reclamo {} ".format(post.get("name")),
                       
        }

        file_claim = request.httprequest.files.get('file_claim')
        ticket_id = request.env['website.support.ticket'].sudo().create(ticket_info)
        
        if file_claim:

            data = file_claim.read()
            name_file = file_claim.filename
            request.env['ir.attachment'].sudo().create({
                'name': name_file,
                'datas': data.encode('base64'),
                'datas_fname': name_file,
                'res_model': 'website.support.ticket',
                'res_id': ticket_id.id
            })            
        
        telefono_claim = request.env['ir.values'].get_default('website.support.settings', 'telefono_claim')
        email_claim_show = request.env['ir.values'].get_default('website.support.settings', 'email_claim_show')
        # Redirecciona a una página de éxito
        return request.render('customer_returns.form_sent', {'claim': ticket_id,'phone':telefono_claim,'email':email_claim_show})
    