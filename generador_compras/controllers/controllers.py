# -*- coding: utf-8 -*-
from odoo import http

# class GeneradorCompras(http.Controller):
#     @http.route('/generador_compras/generador_compras/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/generador_compras/generador_compras/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('generador_compras.listing', {
#             'root': '/generador_compras/generador_compras',
#             'objects': http.request.env['generador_compras.generador_compras'].search([]),
#         })

#     @http.route('/generador_compras/generador_compras/objects/<model("generador_compras.generador_compras"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('generador_compras.object', {
#             'object': obj
#         })