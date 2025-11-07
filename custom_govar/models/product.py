from odoo import models, fields, api

class ProductInherit(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        res = super(ProductInherit, self).create(vals)
        self.env['custom.helpers'].send_email_cp('custom_govar.create_product_email_template','Producto creado',self.env['ir.config_parameter'].sudo().get_param('email_users', ''),res.create_uid.login,res.id,self._name,None)
        return res

    def write(self,vals):

        # if not self.user_has_groups('ventas_govar.not_edit'):
        res = super(ProductInherit, self).write(vals)
        # context = self._context
        # if context.get('params'):
        #     if self._context['params']['action'] in [117,316,325]:
        if vals:
            self.env['custom.helpers'].send_email_cp('custom_govar.write_product_email_template','Producto modificado',self.env['ir.config_parameter'].sudo().get_param('email_users', ''),self.write_uid.login,self.id,'product.template',None)
                
        return res

    def get_url_folio(self):
        # Get the action from context if available, otherwise use a default action
        action = None
        if self._context.get('params') and self._context['params'].get('action'):
            action = self._context['params']['action']
        else:
            # Try to get the default action for res.partner model
            action_record = self.env['ir.actions.act_window'].search([
                ('res_model', '=', 'product.template'),
                ('view_mode', '=', 'form')
            ], limit=1)
            if action_record:
                action = action_record.id
            else:
                # Fallback: use a generic URL without action
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                return f"{base_url}/web#id={self.id}&view_type=form&model=product.template"
        
        return self.env['custom.helpers'].get_url_folio('product.template', action, self.id)
