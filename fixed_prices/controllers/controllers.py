# -*- coding: utf-8 -*-
# from odoo import http


# class FixedPrices(http.Controller):
#     @http.route('/fixed_prices/fixed_prices', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fixed_prices/fixed_prices/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('fixed_prices.listing', {
#             'root': '/fixed_prices/fixed_prices',
#             'objects': http.request.env['fixed_prices.fixed_prices'].search([]),
#         })

#     @http.route('/fixed_prices/fixed_prices/objects/<model("fixed_prices.fixed_prices"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fixed_prices.object', {
#             'object': obj
#         })
