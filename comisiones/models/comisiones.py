# -*- coding: utf-8 -*-

from odoo import api, fields, models
import json


class commision_user(models.Model):
    _inherit = 'res.users'

    pctg_comision = fields.Float(string='Porcentaje Comision',digits = (12,4))


 

class commision_in_invoice(models.Model):
    _inherit = 'account.move'

    commision_paid = fields.Boolean(string="Comision Pagada",help='Campo para saber que factura estan pagadas las comisiones')
    comision = fields.Float(string='Comision(MXN)', compute='_compute_comision', store=True)
    pay_date = fields.Date(string='Fecha Pago',help='Ultimo abono o fecha de pago de una factura', compute='_compute_pay_date', store=True)
    flagcompute = fields.Boolean(
        string='flagcompute',
        compute='_compute_flagcompute'
        )
     
    @api.depends('invoice_payments_widget')
    def _compute_pay_date(self):
        """Compute the payment date from the payments widget"""
        for rec in self:
            if rec.invoice_payments_widget and rec.invoice_payments_widget != 'false':
                try:
                    payments = json.loads(rec.invoice_payments_widget)
                    if isinstance(payments, dict) and payments.get('content'):
                        # Get the latest payment date
                        latest_payment_date = None
                        for payment in payments['content']:
                            if payment.get('date'):
                                latest_payment_date = payment['date']
                        rec.pay_date = latest_payment_date
                    else:
                        rec.pay_date = False
                except (json.JSONDecodeError, TypeError):
                    rec.pay_date = False
            else:
                rec.pay_date = False
    
    @api.depends('user_id', 'user_id.pctg_comision', 'amount_untaxed_signed')
    def _compute_comision(self):
        """Compute the commission based on user percentage"""
        for rec in self:
            if rec.user_id and rec.user_id.pctg_comision:
                rec.comision = rec.amount_untaxed_signed * rec.user_id.pctg_comision
            else:
                rec.comision = 0
    
    def _compute_flagcompute(self):
        """Compute flag for UI purposes"""
        for rec in self:
            rec.flagcompute = bool(rec.pay_date and rec.comision)

    def calculate_payment_date(self):
        """Calculate payment date and commission for paid invoices"""
        account_moves = self.env['account.move'].search([('payment_state', '=', 'paid')])
        for rec in account_moves:
            # Get payment information from the reconciled payments widget
            if rec.invoice_payments_widget and rec.invoice_payments_widget != 'false':
                payments = json.loads(rec.invoice_payments_widget)
                if isinstance(payments, dict) and payments.get('content'):
                    # Get the latest payment date
                    latest_payment_date = None
                    for payment in payments['content']:
                        if payment.get('date'):
                            latest_payment_date = payment['date']
                    if latest_payment_date:
                        rec.pay_date = latest_payment_date
            
            # Calculate commission based on user percentage
            if rec.user_id and rec.user_id.pctg_comision:
                rec.comision = rec.amount_untaxed_signed * rec.user_id.pctg_comision
            else:
                rec.comision = 0