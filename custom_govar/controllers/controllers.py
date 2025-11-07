# -*- coding: utf-8 -*-
# from odoo import http


# class CustomsGovar(http.Controller):
#     @http.route('/customs_govar/customs_govar', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customs_govar/customs_govar/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('customs_govar.listing', {
#             'root': '/customs_govar/customs_govar',
#             'objects': http.request.env['customs_govar.customs_govar'].search([]),
#         })

#     @http.route('/customs_govar/customs_govar/objects/<model("customs_govar.customs_govar"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customs_govar.object', {
#             'object': obj
#         })
