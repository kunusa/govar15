# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class notaCredito(models.Model):
    _name = 'nota.credito'
    name = fields.Char(string='Folio', readonly=True)
    nc_categiria = fields.Many2many(comodel_name='product.category', string='Categorias')
    nc_fecha_inicio = fields.Date(string='Inicio')
    nc_fecha_fin = fields.Date(string='fin')
    nc_producto = fields.Many2one(
        comodel_name='product.product',
        string='Producto',
        default=lambda self: self._default_nc_product()
    )
    notaCreditoLine_ids = fields.One2many(comodel_name='nota.credito.line', inverse_name='notaCredito_id', string='Lineas de Notas')
    state = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('revision', 'Revision'),
        ('cancelar', 'Cancelado'),
        ('aplicado', 'Aplicado')], readonly=True, copy=False, index=True, default='nuevo')

    def validate(self):
        for line in self:
            line.state="revision"

    def cancelar(self):
        for line in self:
            line.state="cancelar"

    def generar_notas(self):
        for line in self:
            for x in line.notaCreditoLine_ids:
                if x.nlc_descuento > 0:
                    taxes_ids = line.nc_producto.taxes_id.ids

                    nota = self.env['account.move'].create({
                        'partner_id': x.ncl_res_partner_id.id,
                        'move_type': 'out_refund',
                        'invoice_user_id': x.ncl_user_id.id,
                        'invoice_origin': 'Descuento',
                        'ref': 'Descuento',
                        'journal_id': x.ncl_user_id.default_journal.id if x.ncl_user_id.default_journal else False,
                        'invoice_date': fields.Date.context_today(self),
                    })

                    self.env['account.move.line'].create({
                        'move_id': nota.id,
                        'product_id': line.nc_producto.id,
                        'name': line.nc_producto.name or 'Descuento',
                        'quantity': 1,
                        'price_unit': x.nlc_monto,
                        'tax_ids': [(6, 0, taxes_ids)],
                        'product_uom_id': line.nc_producto.uom_id.id,
                    })

                    # Recalcular impuestos y términos de pago
                    nota._recompute_dynamic_lines()
            line.state = "aplicado"


    def _default_nc_product(self):
        param = self.env['ir.config_parameter'].sudo().get_param('product')
        try:
            return int(param) if param else False
        except Exception:
            return False

    @api.model
    def create(self, vals):
        if vals.get('name', 'nuevo') == 'nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('descuento.promocion') or 'Nuevo'
        res = super(notaCredito, self).create(vals)
        fecha_inicio = res.nc_fecha_inicio
        fecha_fin = res.nc_fecha_fin
        categorias = res.nc_categiria.ids
        self.fill_lines(res.id, fecha_inicio, fecha_fin, categorias)
        return res
    
    def fill_lines(self, id_header, fecha_inicio, fecha_fin, categorias):
        num = 0
        domain = [
            ('exclude_from_invoice_tab', '=', False),
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
        ]
        if fecha_inicio:
            domain.append(('move_id.invoice_date', '>=', fecha_inicio))
        if fecha_fin:
            domain.append(('move_id.invoice_date', '<=', fecha_fin))
        if categorias:
            domain.append(('product_id.product_tmpl_id.categ_id', 'in', categorias))

        groups = self.env['account.move.line'].read_group(
            domain,
            ['price_subtotal:sum', 'partner_id'],
            ['partner_id']
        )

        for g in groups:
            partner_id = g['partner_id'][0] if g.get('partner_id') else False
            partner = self.env['res.partner'].browse(partner_id) if partner_id else False
            num += 1
            subtotal = g.get('price_subtotal_sum') or g.get('price_subtotal') or 0.0
            vals_line = {
                'ncl_num': num,
                'ncl_res_partner_id': partner_id,
                'ncl_clien_clave': partner.ref if partner else False,
                'notaCredito_id': id_header,
                'ncl_user_id': partner.user_id.id if partner and partner.user_id else False,
                'ncl_subtotal': subtotal,
            }
            self.env['nota.credito.line'].create(vals_line)

	

	

class notaCreditoLine(models.Model):
    _name = 'nota.credito.line'
    ncl_num = fields.Integer(string="N.", readonly=True)
    ncl_res_partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente", readonly=True)
    ncl_clien_clave = fields.Char(string="Clave", readonly=True)
    ncl_user_id = fields.Many2one(comodel_name="res.users", string="Comercial", readonly=True)
    ncl_subtotal = fields.Float(string="Subtotal", readonly=True)
    nlc_descuento = fields.Integer(string="%")
    nlc_monto = fields.Float(string="Monto", compute='_compute_monto', store=True)
    notaCredito_id = fields.Many2one(comodel_name='nota.credito')


    @api.depends('nlc_descuento', 'ncl_subtotal')
    def _compute_monto(self):
        for line in self:
            if line.nlc_descuento:
                line.nlc_monto = (float(line.nlc_descuento) / 100.0) * line.ncl_subtotal
            else:
                line.nlc_monto = 0.0