from odoo import api, fields, models, _, tools
from odoo import exceptions
from odoo.exceptions import UserError
from datetime import datetime, timedelta
ACCOUNT_DOMAIN = "['&', '&', '&', ('deprecated', '=', False), ('internal_type','=','other'), ('company_id', '=', current_company_id), ('is_off_balance', '=', False)]"
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase

class productTemplateTrack(models.Model):
    _inherit = 'product.template'

    @tools.ormcache()
    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('product.product_category_all')

    @tools.ormcache()
    def _get_default_uom_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('uom.product_uom_unit')

    def _get_default_uom_po_id(self):
        return self.default_get(['uom_id']).get('uom_id') or self._get_default_uom_id()

    name = fields.Char('Name', index=True, required=True, translate=True, tracking=True)
    description = fields.Html(
        'Description', translate=True, tracking=True)
    description_purchase = fields.Text(
        'Purchase Description', translate=True, tracking=True)
    description_sale = fields.Text(
        'Sales Description', translate=True, tracking=True,
        help="A description of the Product that you want to communicate to your customers. "
             "This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note")
    detailed_type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Producto')], string='Product Type', default='consu', required=True, tracking=True,
        help='A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')
    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',tracking=True,
        required=True, help="Select category for the current product")
    price = fields.Float(
        'Price', compute='_compute_template_price', inverse='_set_template_price', tracking=True,
        digits='Product Price')
    # list_price: catalog price, user defined
    list_price = fields.Float(
        'Sales Price', default=1.0,
        tracking=True,
        digits='Product Price',
        help="Price at which the product is sold to customers.",
    )
    standard_price = fields.Float(
        'Cost', compute='_compute_standard_price',
        inverse='_set_standard_price', search='_search_standard_price',
        digits='Product Price', groups="base.group_user",
        tracking=True,
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
        In FIFO: value of the next unit that will leave the stock (automatically computed).
        Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
        Used to compute margins on sale orders.""")

    sale_ok = fields.Boolean('Can be Sold', default=True, tracking=True)
    purchase_ok = fields.Boolean('Can be Purchased', default=True, tracking=True)
    pricelist_id = fields.Many2one(
        'product.pricelist', 'Pricelist', store=False, tracking=True,
        help='Technical field. Used for searching on pricelists, not stored in database.')
    uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True, tracking=True,
        help="Default unit of measure used for all stock operations.")
    uom_name = fields.Char(string='Unit of Measure Name', related='uom_id.name', readonly=True,tracking=True)
    uom_po_id = fields.Many2one(
        'uom.uom', 'Purchase UoM',
        default=_get_default_uom_po_id, required=True, tracking=True,
        help="Default unit of measure used for purchase orders. It must be in the same category as the default unit of measure.")
    company_id = fields.Many2one(
        'res.company', 'Company', index=1,tracking=True)
    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id', help="Default taxes used when selling the product.", string='Customer Taxes',
        domain=[('type_tax_use', '=', 'sale')], default=lambda self: self.env.company.account_sale_tax_id,tracking=True)
    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True,tracking=True)
    barcode = fields.Char(
        'Barcode', copy=False,tracking=True,
        help="International Article Number used for product identification.")

    invoice_policy = fields.Selection([
        ('order', 'Ordered quantities'),
        ('delivery', 'Delivered quantities')], string='Invoicing Policy',
        help='Ordered Quantity: Invoice quantities ordered by the customer.\n'
             'Delivered Quantity: Invoice quantities delivered to the customer.',
        default='order',tracking=True)
    supplier_taxes_id = fields.Many2many('account.tax', 'product_supplier_taxes_rel', 'prod_id', 'tax_id', string='Vendor Taxes', help='Default taxes used when buying the product.',
        domain=[('type_tax_use', '=', 'purchase')],tracking=True, default=lambda self: self.env.company.account_purchase_tax_id)
    purchase_method = fields.Selection([
        ('purchase', 'On ordered quantities'),
        ('receive', 'On received quantities'),
    ], string="Control Policy", compute='_compute_purchase_method', default='receive', tracking=True, store=True, readonly=False,
        help="On ordered quantities: Control bills based on ordered quantities.\n"
            "On received quantities: Control bills based on received quantities.")
    volume = fields.Float(
        'Volume', compute='_compute_volume', tracking=True, inverse='_set_volume', digits='Volume', store=True)
    volume_uom_name = fields.Char(string='Volume unit of measure label',tracking=True, compute='_compute_volume_uom_name')
    weight = fields.Float(
        'Weight', compute='_compute_weight', digits='Stock Weight',tracking=True,
        inverse='_set_weight', store=True)
    weight_uom_name = fields.Char(string='Weight unit of measure label',tracking=True, compute='_compute_weight_uom_name')
    property_account_income_id = fields.Many2one('account.account', company_dependent=True,
        string="Income Account",
        domain=ACCOUNT_DOMAIN,
        tracking=True,
        help="Keep this field empty to use the default value from the product category.")
    property_account_expense_id = fields.Many2one('account.account', company_dependent=True,
        string="Expense Account",
        domain=ACCOUNT_DOMAIN,
        tracking=True,
        help="Keep this field empty to use the default value from the product category. If anglo-saxon accounting with automated valuation method is configured, the expense account on the product category will be used.")

    def _set_template_price(self):
        if self._context.get('uom'):
            for template in self:
                value = self.env['uom.uom'].browse(self._context['uom'])._compute_price(template.price, template.uom_id)
                template.write({'list_price': value})
        else:
            self.write({'list_price': self.price})

class stockPickingTrack(models.Model):
    _inherit = 'stock.picking'

    note = fields.Html('Notes', tracking=True)

    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        check_company=True, readonly=True, required=True,  tracking=True,
        states={'draft': [('readonly', False)]})
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, readonly=True, required=True,  tracking=True,
        states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one(
        'res.partner', 'Contact',
        check_company=True, tracking=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    return_picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type for Returns',
        check_company=True,tracking=True)
    move_type = fields.Selection([
        ('direct', 'As soon as possible'), ('one', 'When all products are ready')], 'Shipping Policy',
        default='direct', required=True, tracking=True,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="It specifies goods to be deliver partially or all at once")

class StockMoveLine(models.Model):
    _name = 'stock.move.line'
    _inherit = ['stock.move.line','mail.thread', 'mail.activity.mixin']



    product_uom_qty = fields.Float(
        'Reserved', default=0.0,tracking=True, digits='Product Unit of Measure', required=True, copy=False)
    qty_done = fields.Float('Done', default=0.0,tracking=True, digits='Product Unit of Measure', copy=False)
    date = fields.Datetime('Date', default=fields.Datetime.now, tracking=True)
    reference = fields.Char(related='move_id.reference', store=True, related_sudo=False, readonly=False,tracking=True)
    origin = fields.Char(related='move_id.origin', string='Source',tracking=True)
    product_id = fields.Many2one('product.product', 'Product', tracking=True,ondelete="cascade", check_company=True, domain="[('type', '!=', 'service'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", index=True)
    location_id = fields.Many2one('stock.location', 'From', tracking=True, domain="[('usage', '!=', 'view')]", check_company=True, required=True)
    location_dest_id = fields.Many2one('stock.location', 'To', domain="[('usage', '!=', 'view')]", check_company=True, tracking=True)
    qty_done = fields.Float('Done', default=0.0, digits='Product Unit of Measure', copy=False,tracking=True)

class SaleOrderTrack(models.Model):
    _inherit = 'sale.order'

    def _default_validity_date(self):
        if self.env['ir.config_parameter'].sudo().get_param('sale.use_quotation_validity_days'):
            days = self.env.company.quotation_validity_days
            if days > 0:
                return fields.Date.to_string(datetime.now() + timedelta(days))
        return False

    def _get_default_require_signature(self):
        return self.env.company.portal_confirmation_sign

    def _get_default_require_payment(self):
        return self.env.company.portal_confirmation_pay

    @api.model
    def _default_warehouse_id(self):
        # !!! Any change to the default value may have to be repercuted
        # on _init_column() below.
        return self.env.user._get_default_warehouse_id()

    name = fields.Char(string='Order Reference', tracking=True,required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    origin = fields.Char(string='Source Document',tracking=True, help="Reference of the document that generated this sales order request.")
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    reference = fields.Char(string='Payment Ref.',tracking=True, copy=False,
        help='The payment communication of this sale order.')    
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Address',
        readonly=True, required=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",tracking=True)
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', readonly=True, required=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",tracking=True)
    date_order = fields.Datetime(string='Order Date', tracking=True, required=True, readonly=True, index=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, copy=False, default=fields.Datetime.now, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    validity_date = fields.Date(string='Expiration',tracking=True, readonly=True, copy=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                default=_default_validity_date)
    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', check_company=True,  # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",tracking=True)

    signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024,tracking=True)
    signed_by = fields.Char('Signed By', help='Name of the person that signed the SO.', copy=False,tracking=True)
    signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False,tracking=True)
    require_signature = fields.Boolean('Online Signature', default=_get_default_require_signature, readonly=True,tracking=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help='Request a online signature to the customer in order to confirm orders automatically.')
    require_payment = fields.Boolean('Online Payment', default=_get_default_require_payment, readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},tracking=True,
        help='Request an online payment to the customer in order to confirm orders automatically.')
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True,tracking=True)
    tag_ids = fields.Many2many('crm.tag', 'sale_order_tag_rel', 'order_id', 'tag_id', string='Tags',tracking=True)

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string='Fiscal Position',tracking=True,
        domain="[('company_id', '=', company_id)]", check_company=True,
        help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices."
        "The default value comes from the customer.")
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account',
        compute='_compute_analytic_account_id', store=True,
        readonly=False, copy=False, check_company=True,  # Unrequired company
        states={'sale': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The analytic account related to a sales order.",tracking=True)
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,  # Unrequired company
        required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", tracking=True,
        help="If you change the pricelist, only newly added lines will be affected.")

class PurchaseOrderTrack(models.Model):
    _inherit = 'purchase.order'


    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)


    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Urgent')], 'Priority', default='0', index=True, tracking=True)
    origin = fields.Char('Source Document', copy=False,tracking=True,
        help="Reference of the document that generated this purchase order "
             "request (e.g. a sales order)")
    partner_ref = fields.Char('Vendor Reference', copy=False,tracking=True,
        help="Reference of the sales order or bid sent by the vendor. "
             "It's used to do the matching when you receive the "
             "products as this reference is usually written on the "
             "delivery order sent by your vendor.")
    date_order = fields.Datetime('Order Deadline', required=True, states=READONLY_STATES, index=True, copy=False, default=fields.Datetime.now,
        help="Depicts the date within which the Quotation should be confirmed and converted into a purchase order.")
    date_approve = fields.Datetime('Confirmation Date', readonly=1, index=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES, change_default=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    dest_address_id = fields.Many2one('res.partner', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", string='Dropship Address', states=READONLY_STATES,
        help="Put an address if you want to deliver directly from the vendor to the customer. "
             "Otherwise, keep empty to deliver to your own company.")
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, states=READONLY_STATES,
        default=lambda self: self.env.company.currency_id.id,tracking=True)
    date_planned = fields.Datetime(
        string='Receipt Date', index=True,tracking=True, copy=False, compute='_compute_date_planned', store=True, readonly=False,
        help="Delivery date promised by vendor. This date is used to determine expected arrival of products.")
    fiscal_position_id = fields.Many2one('account.fiscal.position', tracking=True, string='Fiscal Position', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    tax_country_id = fields.Many2one(
        comodel_name='res.country',
        compute='_compute_tax_country_id',
        # Avoid access error on fiscal position, when reading a purchase order with company != user.company_ids
        compute_sudo=True, tracking=True,
        help="Technical field to filter the available taxes depending on the fiscal country and fiscal position.")
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms',tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', states={'done': [('readonly', True)]},tracking=True, help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=Purchase.READONLY_STATES, required=True, default=_default_picking_type, domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
        help="This will determine operation type of incoming shipment",tracking=True)
    notes = fields.Html('Terms and Conditions',tracking=True)

class resPartnerTrack(models.Model):
    _inherit = 'res.partner'