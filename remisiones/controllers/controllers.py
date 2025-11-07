# -*- coding: utf-8 -*-
# from odoo import http


# class Remisiones(http.Controller):
#     @http.route('/remisiones/remisiones', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/remisiones/remisiones/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('remisiones.listing', {
#             'root': '/remisiones/remisiones',
#             'objects': http.request.env['remisiones.remisiones'].search([]),
#         })

#     @http.route('/remisiones/remisiones/objects/<model("remisiones.remisiones"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('remisiones.object', {
#             'object': obj
#         })
