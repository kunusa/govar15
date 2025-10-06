# -*- coding: utf-8 -*-
# from odoo import http


# class Comisiones(http.Controller):
#     @http.route('/comisiones/comisiones', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/comisiones/comisiones/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('comisiones.listing', {
#             'root': '/comisiones/comisiones',
#             'objects': http.request.env['comisiones.comisiones'].search([]),
#         })

#     @http.route('/comisiones/comisiones/objects/<model("comisiones.comisiones"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('comisiones.object', {
#             'object': obj
#         })
