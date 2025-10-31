from odoo import api, fields, models, _
from odoo import exceptions
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class accountMoveInherit(models.Model):
    _inherit = 'account.move'

    email_message = fields.Char("Mensaje enviado")
    ref = fields.Char(string='Referencia proveedor', copy=False, tracking=True)
    
    # Campo personalizado para agregar pedidos de compra (similar a Odoo 10)
    purchase_id_custom = fields.Many2one(
        'purchase.order',
        string='Añadir un pedido de compra',
        store=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('id', 'in', allowed_purchase_ids)]",
        help="Seleccione un pedido de compra del mismo proveedor para agregar líneas recibidas y no facturadas"
    )

    # Lista de pedidos de compra permitidos para seleccionar en la factura
    allowed_purchase_ids = fields.Many2many(
        'purchase.order',
        compute='_compute_allowed_purchase_ids',
        string='Pedidos de compra disponibles',
        store=False,
    )

    def _get_purchase_domain(self):
        """
        Calcula el dominio para el campo purchase_id_custom.
        Retorna el dominio para filtrar pedidos de compra con productos por facturar.
        """
        # Solo ejecutar si es factura de proveedor
        if not self.move_type or self.move_type != 'in_invoice':
            return [('id', '=', False)]
        
        # Obtener las líneas de pedido de compra que ya están en la factura
        invoice_lines = self.line_ids.filtered(lambda l: l.exclude_from_invoice_tab == False)
        purchase_line_ids = invoice_lines.mapped('purchase_line_id')
        purchase_ids = invoice_lines.mapped('purchase_line_id.order_id')
        
        # Dominio base: solo pedidos con estado "to invoice" (tienen productos por facturar)
        # y que pertenecen al mismo proveedor
        domain = [('invoice_status', '=', 'to invoice')]
        if self.partner_id:
            domain += [('partner_id', 'child_of', self.partner_id.id)]
        if purchase_ids:
            # Excluir pedidos que ya tienen todas sus líneas en la factura
            domain += [('id', 'not in', purchase_ids.ids)]
        
        return domain



    @api.depends('move_type', 'state', 'partner_id', 'line_ids.purchase_line_id', 'line_ids.exclude_from_invoice_tab')
    def _compute_allowed_purchase_ids(self):
        """
        Calcula los pedidos de compra disponibles para el campo purchase_id_custom.
        Se ejecuta al abrir/crear la factura y cuando cambian los campos relevantes.
        """
        PurchaseOrder = self.env['purchase.order']
        for move in self:
            if move.move_type != 'in_invoice' or not move.partner_id:
                move.allowed_purchase_ids = False
                continue

            invoice_lines = move.line_ids.filtered(lambda l: not l.exclude_from_invoice_tab)
            purchase_ids = invoice_lines.mapped('purchase_line_id.order_id')

            domain = [
                ('invoice_status', '=', 'to invoice'),
                ('state', 'in', ['purchase', 'done']),
                ('partner_id', 'child_of', move.partner_id.id),
            ]
            if purchase_ids:
                domain += [('id', 'not in', purchase_ids.ids)]

            move.allowed_purchase_ids = PurchaseOrder.search(domain)

    @api.onchange('move_type', 'state', 'partner_id', 'line_ids')
    def _onchange_allowed_purchase_ids(self):
        """
        Define el dominio para los pedidos de compra disponibles.
        Se ejecuta cuando cambia move_type, state, partner_id o line_ids.
        """
        result = {}
        domain = self._get_purchase_domain()
        result['domain'] = {'purchase_id_custom': domain}
        return result

    def action_post(self):
        """
        Hereda el método action_post y agrega el envío de correo
        """
        if self.move_type == 'in_invoice' and not self.ref:
            raise UserError(_('La referencia de proveedor es obligatoria para confirmar la factura'))
        # Llamar al método original
        result = super().action_post()
        # Enviar correo después de confirmar la factura
        self.send_email_company()
        
        return result

    def delete_lines(self):
        """Enfocarse en la factura en lugar de las líneas individuales"""
        for invoice in self:
            lines_to_delete = invoice.invoice_line_ids.filtered(lambda l: l.line_delete)
            
            if not lines_to_delete:
                continue
                            
            # Crear nueva lista de líneas sin las marcadas para eliminar
            new_line_vals = []
            for line in invoice.invoice_line_ids:
                if line not in lines_to_delete:
                    new_line_vals.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'quantity': line.quantity,
                        'price_unit': line.price_unit,
                        'account_id': line.account_id.id,
                        'tax_ids': [(6, 0, line.tax_ids.ids)],
                    }))
            
            # Reemplazar todas las líneas
            invoice.write({
                'invoice_line_ids': [(5, 0, 0)] + new_line_vals
            })
            
    def send_email_company(self):
        """
        Envía correo cuando se crea una factura para la empresa
        """
        # Obtener el correo de configuración
        email_company = self.env['ir.config_parameter'].sudo().get_param('email_company', '')
        
        if not email_company:
            return False
            
        # Verificar si es factura de cliente y el RFC coincide
        if self.move_type == 'out_invoice' and self.partner_id.vat == self.company_id.rfc_to_send:
            subject = f'Factura creada para {self.partner_id.name}'
            self.env['custom.helpers'].send_email_cp(
                'custom_govar.create_invoice_customer_company_email_move',
                subject,
                email_company,
                self.company_id.email,
                self.id,
                'account.move',
                None
            )
        # Verificar si es factura de proveedor y el RFC coincide
        elif self.move_type == 'in_invoice' and self.partner_id.vat == self.company_id.rfc_to_send:
            subject = f'Factura creada para {self.partner_id.name}'
            self.env['custom.helpers'].send_email_cp(
                'custom_govar.create_invoice_supplier_company_email_template',
                subject,
                email_company,
                self.company_id.email,
                self.id,
                'account.move',
                None
            )

    def get_url_folio(self):
        """
        Obtiene la URL del folio de la factura
        """
        try:
            # Intentar obtener la acción del contexto web
            action_id = self._context.get('params', {}).get('action')
            if action_id:
                return self.env['custom.helpers'].get_url_folio('account.move', action_id, self.id)
        except (KeyError, AttributeError):
            pass
        
        # Si no hay contexto web, generar URL directa
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web#id={self.id}&model=account.move&view_type=form"

    def validate_origin(self,vals):

        if not self.env.user.has_group('custom_govar.craete_several_invoices_so'):
            if not vals.get('invoice_origin'):
                raise exceptions.UserError("No se puede generar una factura sin una SO validada")

    @api.model
    def create(self, vals):
        self.validate_origin(vals)
        type_account = self._context.get('type_account')
        if  vals.get('move_type') == 'in_invoice':
            del vals['ref']

        if  vals.get('payment_reference'):
            del vals['payment_reference']
        res = super().create(vals)
        
        # Llamar directamente al método para establecer el dominio cuando se crea una factura de proveedor
        if res.move_type == 'in_invoice':
            res._onchange_allowed_purchase_ids()
            name_origin = res.invoice_line_ids.mapped('purchase_line_id.order_id')
            res.document_origin = name_origin

        if not self.env.user.default_journal.id:
            raise UserError(_('Favor de definir el diario(serie de facturacón) del usuario.'))

        if res.move_type in ['out_invoice','out_refund']:
            res.journal_id = self.env.user.default_journal.id

        if res.move_type == 'out_refund' or res.move_type == 'in_refund':

            if vals.get('move_type') == "out_refund":
                if type_account in ['discount_purchase','refaund_purchase']:
                    raise exceptions.UserError("No se puede generar una nota de crédito con una cuenta de compras")
                
                # Obtener cuentas configuradas para ventas
                if type_account == 'discount_sale':
                    account_id = self.env['ir.config_parameter'].sudo().get_param('discount_sale_account', '')
                elif type_account == 'refaund_sale':
                    account_id = self.env['ir.config_parameter'].sudo().get_param('refaund_sale_account', '')
                else:
                    account_id = False
                
            if vals.get('move_type') == "in_refund":
                if type_account in ['discount_sale','refaund_sale']:
                    raise exceptions.UserError("No se puede generar una nota de crédito con una cuenta de ventas")
                
                # Obtener cuentas configuradas para compras
                if type_account == 'discount_purchase':
                    account_id = self.env['ir.config_parameter'].sudo().get_param('discount_purchase_account', '')
                elif type_account == 'refaund_purchase':
                    account_id = self.env['ir.config_parameter'].sudo().get_param('refaund_purchase_account', '')
                else:
                    account_id = False
                
            # Aplicar la cuenta a las líneas si está configurada
            if account_id:
                self._apply_account_to_lines(res, account_id)

        if res.move_type == 'in_invoice':
            reference = self.env['account.move'].search([('partner_id','=',res.partner_id.id),('ref','=',vals.get('ref')),('move_type','=',res.move_type),('state','=','posted')], limit = 1)
            if reference and reference.ref:
                raise UserError(_("Ya existe una factura con la referencia '{}'".format(vals.get('ref'))))
        
        if res.move_type == 'in_refund':	
            if not self._context.get('reference'):
                raise UserError(_("La referencia es obligatoria en caso de una nota de crédito de un proveedor"))
            
            reference = self.env['account.move'].search([('partner_id','=',vals.get('partner_id')),('ref','=',self._context.get('reference')),('move_type','=',res.move_type),('state','=','posted')], limit = 1)
            if reference and res.move_type == 'in_refund':
                raise UserError(_("Ya existe una nota de crédito con la referencia '{}'".format(self._context.get('reference'))))		
            
            res.ref = self._context.get('reference')
                    
        return res
    

        
    def _apply_account_to_lines(self, move, account_id):
        """
        Aplica la cuenta especificada a todas las líneas de la factura
        """

        id_credit = self.env['account.account'].search([('id','=',int(account_id))], limit = 1)
        try:
            for line in move.invoice_line_ids:
                line.account_id = id_credit.id
        except Exception as e:
            # Log del error pero no interrumpir el proceso
            pass

    def change_account_line_sales(self):
        if self.invoice_line_ids and self.move_type == 'out_invoice':
            type_account = 'sales'
        else:
            type_account = 'buys'
        account = self.env['number.account'].search([(type_account,'=',True)],limit = 1)
        for invoice_line in self.invoice_line_ids:
            invoice_line.account_id = account.account_id

    @api.onchange('purchase_id_custom')
    def _onchange_purchase_id_custom(self):

        self._onchange_allowed_purchase_ids()
        if not self.purchase_id_custom or self.move_type != 'in_invoice':
            return

        # Verificar que el proveedor coincide
        if self.partner_id and self.purchase_id_custom.partner_id != self.partner_id:
            return {
                'warning': {
                    'title': _('Advertencia'),
                    'message': _('El pedido de compra seleccionado no pertenece al mismo proveedor que la factura.'),
                }
            }

        # Obtener las líneas del pedido de compra que ya están en la factura
        # En Odoo 15, usar line_ids para facturas y invoice_line_ids para compatibilidad
        invoice_lines = self.line_ids.filtered(lambda l: l.exclude_from_invoice_tab == False)
        existing_purchase_lines = invoice_lines.mapped('purchase_line_id')
        
        # Filtrar líneas que:
        # 1. No están ya en la factura
        # 2. Han sido recibidas (qty_received > 0)
        # 3. Tienen cantidad pendiente por facturar (qty_to_invoice > 0)
        # 4. No son de tipo display (section/note)
        po_lines_to_add = self.purchase_id_custom.order_line.filtered(
            lambda l: l not in existing_purchase_lines
            and not l.display_type
            and float_compare(l.qty_received, 0.0, precision_rounding=l.product_uom.rounding) > 0
            and float_compare(l.qty_to_invoice, 0.0, precision_rounding=l.product_uom.rounding) > 0
        )

        if not po_lines_to_add:
            self.purchase_id_custom = False
            return {
                'warning': {
                    'title': _('Sin líneas disponibles'),
                    'message': _('No hay líneas recibidas y no facturadas disponibles en este pedido de compra.'),
                }
            }

        # Preparar las nuevas líneas de factura
        new_lines = self.env['account.move.line']
        sequence = max(invoice_lines.mapped('sequence')) + 1 if invoice_lines else 10
        
        for po_line in po_lines_to_add:
            # Usar el método estándar de Odoo 15 para preparar la línea
            line_vals = po_line._prepare_account_move_line(self)
            line_vals.update({'sequence': sequence})
            new_line = new_lines.new(line_vals)
            sequence += 1
            # Obtener la cuenta correcta
            new_line.account_id = new_line._get_computed_account()
            new_line._onchange_price_subtotal()
            new_lines += new_line

        if new_lines:
            new_lines._onchange_mark_recompute_taxes()
            # Agregar las nuevas líneas a las líneas existentes
            # En Odoo 15, usar line_ids (el campo estándar de account.move)
            self.line_ids = self.line_ids + new_lines
            
            # Actualizar el origen de la factura
            # Obtener todas las líneas de factura actualizadas
            updated_invoice_lines = self.line_ids.filtered(lambda l: l.exclude_from_invoice_tab == False)
            purchase_orders = updated_invoice_lines.mapped('purchase_line_id.order_id')
            if purchase_orders:
                origins = purchase_orders.mapped('name')
                if self.invoice_origin:
                    existing_origins = set(self.invoice_origin.split(', '))
                    new_origins = set(origins)
                    all_origins = existing_origins | new_origins
                    self.invoice_origin = ', '.join(sorted(all_origins))
                else:
                    self.invoice_origin = ', '.join(origins)

        # Limpiar el campo después de usar
        self.purchase_id_custom = False


class accountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    line_delete = fields.Boolean(string=' ', default=False, store=True)


    def write(self, vals):
        
        res = super(accountMoveLineInherit, self).write(vals)

        if not self.env.user.has_group('custom_govar.craete_several_invoices_so'):
            if self.move_id.invoice_origin  and self.move_id.move_type == 'out_invoice' and self.move_id.state == 'draft':

                if vals.get('quantity') and self.move_id.invoice_origin [:1] == 'S':
                    raise exceptions.UserError("No se puede modificar la cantidad de un producto \n de una factura con una SO validada")
                
                if vals.get('name'):
                    raise exceptions.UserError("No se puede modificar la descripción de un producto \n de una factura con una SO validada")
                if vals.get('price_unit'):
                    raise exceptions.UserError("No se puede modificar el precio de un producto \n de una factura con una SO validada")  

                if self.product_id.product_tmpl_id.type == 'product':
                    raise exceptions.UserError("No se puede agregar un producto de tipo almacenable \n de una factura con una SO validada")


        return res

    def unlink(self):
        if not self.env.user.has_group('custom_govar.craete_several_invoices_so') and self.move_id.move_type == 'out_invoice':
            for rec in self:
                if rec.product_id.product_tmpl_id.type == 'product':
                    raise exceptions.UserError("No se puede eliminar un producto tipo almacenable  \n de una factura con una SO validada")

        return super(accountMoveLineInherit, self).unlink()
