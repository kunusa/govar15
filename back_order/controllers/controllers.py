# -*- coding: utf-8 -*-
from odoo import http

# class BackOrder(http.Controller):
#     @http.route('/back_order/back_order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/back_order/back_order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('back_order.listing', {
#             'root': '/back_order/back_order',
#             'objects': http.request.env['back_order.back_order'].search([]),
#         })

#     @http.route('/back_order/back_order/objects/<model("back_order.back_order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('back_order.object', {
#             'object': obj
#         })