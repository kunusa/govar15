# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    strict_range = fields.Boolean(string='Use Strict Range', default=True,
                                  help='Use this if you want to show TB with retained earnings section')
    bucket_1 = fields.Integer(string='Bucket 1', required=True, default=30)
    bucket_2 = fields.Integer(string='Bucket 2', required=True, default=60)
    bucket_3 = fields.Integer(string='Bucket 3', required=True, default=90)
    bucket_4 = fields.Integer(string='Bucket 4', required=True, default=120)
    bucket_5 = fields.Integer(string='Bucket 5', required=True, default=180)
    date_range = fields.Selection(
        [('today', 'Hoy'),
         ('this_week', 'Esta Semana'),
         ('this_month', 'Este Mes'),
         ('this_quarter', 'Este Cuarto'),
         ('this_financial_year', 'Este Año Fiscal'),
         ('yesterday', 'Ayer'),
         ('last_week', 'La Semana Pasada'),
         ('last_month', 'El Mes Pasado'),
         ('last_quarter', 'El Cuarto Pasado'),
         ('last_financial_year', 'El Año Fiscal Anterior')],
        string='Rango de fechas predeterminado', default='this_financial_year', required=True
    )
    financial_year = fields.Selection([
        ('april_march','1 Abril al 31 de Marzo'),
        ('july_june','1 julio al 30 de Junio'),
        ('january_december','1 Enero al 31 de Diciembre')
        ], string='Año fiscal', default='january_december', required=True)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    excel_format = fields.Char(string='Excel format', default='_ * #,##0.00_) ;_ * - #,##0.00_) ;_ * "-"??_) ;_ @_ ', required=True)

class ins_account_financial_report(models.Model):
    _name = "ins.account.financial.report"
    _description = "Account Report"

    @api.depends('parent_id', 'parent_id.level')
    def _get_level(self):
        '''Returns a dictionary with key=the ID of a record and value = the level of this
           record in the tree structure.'''
        for report in self:
            level = 0
            if report.parent_id:
                level = report.parent_id.level + 1
            report.level = level

    def _get_children_by_order(self, strict_range):
        '''returns a recordset of all the children computed recursively, and sorted by sequence. Ready for the printing'''
        res = self
        children = self.search([('parent_id', 'in', self.ids)], order='sequence ASC')
        if children:
            for child in children:
                res += child._get_children_by_order(strict_range)
        if not strict_range:
            res -= self.env.ref('account_dynamic_reports.ins_account_financial_report_unallocated_earnings0')
            res -= self.env.ref('account_dynamic_reports.ins_account_financial_report_equitysum0')
        return res

    name = fields.Char('Nombre del Reporte', required=True, translate=True)
    parent_id = fields.Many2one('ins.account.financial.report', 'Parent')
    children_ids = fields.One2many('ins.account.financial.report', 'parent_id', 'Account Report')
    sequence = fields.Integer('Sequence')
    level = fields.Integer(compute='_get_level', string='Nivel', store=True)
    type = fields.Selection([
        ('sum', 'Vista'),
        ('accounts', 'Cuentas'),
        ('account_type', 'Tipo de cuenta'),
        ('account_report', 'Valor del reporte'),
        ], 'Type', default='sum')
    account_ids = fields.Many2many('account.account', 'ins_account_account_financial_report', 'report_line_id', 'account_id', 'Accounts')
    account_report_id = fields.Many2one('ins.account.financial.report', 'Valor del reporte')
    account_type_ids = fields.Many2many('account.account.type', 'ins_account_account_financial_report_type', 'report_id', 'account_type_id', 'Account Types')
    sign = fields.Selection([('-1', 'Reverse balance sign'), ('1', 'Preserve balance sign')], 'Firma en reporte', required=True, default='1',
                            help='Para las cuentas que normalmente tienen más débitos que créditos y que le gustaría imprimir como montos negativos en sus informes, debe invertir el signo del saldo; ej.: Cuenta de gastos. Lo mismo se aplica a las cuentas que normalmente se acreditan más que se cargan y que le gustaría imprimir como cantidades positivas en sus informes; ej.: Cuenta de ingresos.')
    range_selection = fields.Selection([
        ('from_the_beginning', 'From the Beginning'),
        ('current_date_range', 'Based on Current Date Range'),
        ('initial_date_range', 'Based on Initial Date Range'),
        ('balance_general','Balance General'),
        ('period_general_balance','Balance General por Periodos')],
        help='"From the beginning" will select all the entries before and on the date range selected.'
             '"Based on Current Date Range" will select all the entries strictly on the date range selected'
             '"Based on Initial Date Range" will select only the initial balance for the selected date range'
             '"Balance General" Seleccionara el balance inicial + saldo actual para proporcionarnos un saldo final',
        string='Custom Date Range')
    display_detail = fields.Selection([
        ('no_detail', 'Sin detalle'),
        ('detail_flat', 'Mostar secundario Plano'),
        ('detail_with_hierarchy', 'MOstar secundario con jerarquía')
        ], 'Mostrar detalles', default='detail_flat')
    style_overwrite = fields.Selection([
        ('0', 'Formateo automático'),
        ('1', 'Título principal 1 (negrita, subrayado)'),
        ('2', 'Título 2 (negrita)'),
        ('3', 'Título 3 (negrita, más pequeño)'),
        ('4', 'Texto Normal'),
        ('5', 'Texto en cursiva (más pequeño)'),
        ('6', 'Texto más pequeño'),
        ], 'Estilo del reporte financiero', default='0',
        help="Puede configurar aquí el formato en el que desea que se muestre este registro. Si deja el formato automático, se calculará en función de la jerarquía de informes financieros (campo de cálculo automático 'nivel').")


class AccountAccount(models.Model):
    _inherit = 'account.account'

    def get_cashflow_domain(self):
        cash_flow_id = self.env.ref('account_dynamic_reports.ins_account_financial_report_cash_flow0')
        if cash_flow_id:
            return [('parent_id.id', '=', cash_flow_id.id)]

    cash_flow_category = fields.Many2one('ins.account.financial.report', string="Tipo de flujo de caja", domain=get_cashflow_domain)

    @api.onchange('cash_flow_category')
    def onchange_cash_flow_category(self):
        # Add account to cash flow record to account_ids
        if self._origin and self._origin.id:
            self.cash_flow_category.write({'account_ids': [(4, self._origin.id)]})
            self.env.ref(
                'account_dynamic_reports.ins_account_financial_report_cash_flow0').write(
                {'account_ids': [(4, self._origin.id)]})
        # Remove account from previous category
        # In case of changing/ removing category
        if self._origin.cash_flow_category:
            self._origin.cash_flow_category.write({'account_ids': [(3, self._origin.id)]})
            self.env.ref(
                'account_dynamic_reports.ins_account_financial_report_cash_flow0').write(
                {'account_ids': [(3, self._origin.id)]})


class CommonXlsxOut(models.TransientModel):
    _name = 'common.xlsx.out'

    filedata = fields.Binary('Descargar archivo', readonly=True)
    filename = fields.Char('Nombre del archivo', size=64, readonly=True)