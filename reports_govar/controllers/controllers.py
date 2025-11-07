# -*- coding: utf-8 -*-
# from odoo import http


# class ReportsGovar(http.Controller):
#     @http.route('/reports_govar/reports_govar', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/reports_govar/reports_govar/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('reports_govar.listing', {
#             'root': '/reports_govar/reports_govar',
#             'objects': http.request.env['reports_govar.reports_govar'].search([]),
#         })

#     @http.route('/reports_govar/reports_govar/objects/<model("reports_govar.reports_govar"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('reports_govar.object', {
#             'object': obj
#         })
