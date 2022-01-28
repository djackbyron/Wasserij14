# -*- coding: utf-8 -*-

import datetime
from lxml import etree
from odoo import models, fields, api


class WashType(models.Model):
    _name = "em.laundry.mgt.wash.type"

    name = fields.Char('Washing Type')
    washing_charge = fields.Float('Washing Charge')
    responsible_person = fields.Many2one('res.users', string='Responsible Person')


class OtherThanWash(models.Model):
    _name = "em.laundry.other.than.wash"

    name = fields.Char('Name')
    work_charge = fields.Float('Charge')
    responsible_person = fields.Many2one('res.users', string='Responsible Person')


class Washings(models.Model):
    _name = "em.laundry.mgt.washings"

    name = fields.Char('Work Name')
    responsible_person = fields.Many2one('res.users', string='Responsible Person')
    date_time = fields.Datetime('Date-Time')
    cloth = fields.Char('Cloth Name')
    cloth_count = fields.Integer('No. Of cloths')
    description = fields.Text('Description')
    order_id = fields.Many2one('sale.order')
    order_line_id = fields.Many2one('sale.order.line')
    washing_states = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, default='draft', copy=False)
    laundry_track_code = fields.Char('Tracking Code')
    is_make_over = fields.Boolean('Make Over')
    is_make_over_text = fields.Char()

    def start_wash(self):
        self.washing_states = 'process'
        if not self.is_make_over:
            self.order_line_id.state_per_washing = 'wash'

    def finish_wash(self):
        self.washing_states = 'done'
        line = self.order_line_id

        if line.other_than_wash_ids:
            obj_ids = self.env['em.laundry.mgt.washings'].search(
                [('is_make_over', '=', True), ('order_line_id', '=', line.id)])
            if obj_ids:
                for obj in obj_ids:
                    if obj.washing_states == 'done':
                        pass
                    else:
                        return
                    self.order_line_id.state_per_washing = 'done'
            else:
                for other_than in line.other_than_wash_ids:
                    if line.state_per_washing != 'other_than_wash':
                        self.env['em.laundry.mgt.washings'].create({'name': other_than.name,
                                                                    'responsible_person': other_than.responsible_person.id,
                                                                    'date_time': datetime.datetime.now(),
                                                                    'cloth': line.product_id.name,
                                                                    'cloth_count': line.dress_count_in,
                                                                    'description': line.name,
                                                                    'order_id': line.order_id.id,
                                                                    'order_line_id': line.id,
                                                                    'is_make_over': True,
                                                                    'is_make_over_text': 'Make Over',
                                                                    'laundry_track_code': line.laundry_track_code
                                                                    })
                self.order_line_id.state_per_washing = 'other_than_wash'
        else:
            self.order_line_id.state_per_washing = 'done'

    def cancel_wash(self):
        self.washing_states = 'cancel'
        self.order_line_id.state_per_washing = 'cancel'


class LaundryTrackTag(models.AbstractModel):
    _name = 'laundry.track.code'

    def _get_report_values(self, docids, data=None):
        return data


class SaleOrderExtend(models.Model):
    _inherit = "sale.order"

    is_laundry_order = fields.Boolean()
    responsible_person = fields.Many2one('res.users', string='Laundry Person')
    state = fields.Selection(
        selection_add=[('draft',), ('order', 'Laundry Order'), ('process', 'Processing'), ('sale',), ('done',),
                       ('complete', 'Completed'), ('return', 'Returned'),
                       ('cancel', 'Cancelled')])
    washing_count = fields.Integer('Washings', compute='get_washing_count')
    all_done = fields.Boolean()

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleOrderExtend, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                            submenu=submenu)
        is_laundry_order = self._context.get('default_is_laundry_order', False)

        if is_laundry_order:
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//page[@name='order_lines']/field[@name='order_line']/tree/field[@name='product_id']")
            for node in nodes:
                node.set('string', "Cloth Name")
                node.set('domain', "[('type','=','service')]")
            res['arch'] = etree.tostring(doc)
        return res

    def _create_invoices(self, grouped=False, final=False):
        result = super(SaleOrderExtend, self)._create_invoices(grouped, final)
        if self.is_laundry_order:
            for line in self.order_line:
                for invoice_line_id in line.invoice_lines:
                    invoice_line_id.move_id.is_laundry_invoice = True
                    for invoice_line in result.invoice_line_ids:
                        if invoice_line.id == invoice_line_id.id:
                            invoice_line.wash_type_id = line.wash_type_id
                            invoice_line.other_than_wash_ids = line.other_than_wash_ids

        return result

    def generate_invoice(self):
        self._create_invoices()
        self.state = 'complete'

    def action_confirm(self):
        if self.is_laundry_order and self.state != 'process':
            self.state = 'order'
        else:
            result = super(SaleOrderExtend, self).action_confirm()
            self.all_done = False

            return result

    def set_to_process(self):
        if self.is_laundry_order:
            for line in self.order_line:
                self.env['em.laundry.mgt.washings'].create({'name': line.wash_type_id.name,
                                                            'responsible_person': line.wash_type_id.responsible_person.id,
                                                            'date_time': datetime.datetime.now(),
                                                            'cloth': line.product_id.name,
                                                            'cloth_count': line.dress_count_in,
                                                            'description': line.name,
                                                            'order_id': line.order_id.id,
                                                            'order_line_id': line.id,
                                                            'is_make_over': False,
                                                            'is_make_over_text': 'Washing',
                                                            'laundry_track_code': line.laundry_track_code
                                                            })
            self.state = 'process'

    def washings_list(self):
        return {
            'name': 'Washings',
            'type': 'ir.actions.act_window',
            'res_model': 'em.laundry.mgt.washings',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_id': False,
            'target': 'current',
            'domain': [('order_id', '=', self.id)],
            'context': {'group_by': 'is_make_over_text'}

        }

    def get_washing_count(self):
        for res in self:
            ls = self.env['em.laundry.mgt.washings'].search([('order_id', '=', res.id)]).ids
            res.washing_count = len(ls)
            if res.all_done:
                for line in res.order_line:
                    if line.state_per_washing == 'return':
                        pass
                    else:
                        return
                res.state = 'return'
            else:
                for line in res.order_line:
                    if line.state_per_washing == 'done':
                        pass
                    else:
                        return
                if res.order_line:
                    res.all_done = True

    def return_laundry(self):
        return_lines = []
        for rec in self.order_line:
            return_lines.append([0, 0, {'dress_id': rec.product_id.id,
                                        'qty_in': rec.dress_count_in,
                                        'qty_out': rec.dress_count_out,
                                        'sale_order_line_id': rec.id,
                                        'status': rec.state_per_washing
                                        }])
        res_id = (
            self.env['em.laundry.mgt.laundry.return'].create(
                {'laundry_lines_ids': return_lines})).id
        return {
            'name': 'Returns',
            'type': 'ir.actions.act_window',
            'res_model': 'em.laundry.mgt.laundry.return',
            'view_mode': 'form',
            'view_id': False,
            'res_id': res_id,
            'target': 'new',
        }

    def print_tracking_code(self):
        order_lines = []
        for line in self.order_line:
            extra_work = []
            for extra in line.other_than_wash_ids:
                extra_work.append(extra.name)
            order_lines.append({'cloth_name': line.product_id.name,
                                'quantity_in': line.dress_count_in,
                                'laundry_track_code': line.laundry_track_code,
                                'wash_type': line.wash_type_id.name,
                                'other_than_wash': extra_work})

        data = {
            'customer_name': self.partner_id.name,
            'laundry_person': self.responsible_person.name,
            'order_lines': order_lines
        }
        return self.env.ref('em_laundry_management.print_tracking_code_tag_action').report_action([],
                                                                                                  data={'rec': data})


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    wash_type_id = fields.Many2one('em.laundry.mgt.wash.type', string='Wash Type')
    other_than_wash_ids = fields.Many2many('em.laundry.other.than.wash', string='Other Than Wash')
    dress_count_in = fields.Integer('Quantity In', default=1)
    dress_count_out = fields.Integer('Quantity Out')
    state_per_washing = fields.Selection([
        ('draft', 'Draft'),
        ('wash', 'Washing'),
        ('other_than_wash', 'Make Over'),
        ('done', 'Done'),
        ('return', 'Returned'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, default='draft')
    laundry_track_code = fields.Char('Tracking Code')

    @api.onchange('product_id')
    def product_id_onchange(self):
        if self.order_id.is_laundry_order:
            wash_type_ids = []
            self.wash_type_id = None
            self.other_than_wash_ids = None
            self.dress_count_in = 1
            res = {
                'domain': {'wash_type_id': []}
            }
            if self.product_id.washing_charge_ids:
                for wash_type_charge_id in self.product_id.washing_charge_ids:
                    wash_type_ids.append(wash_type_charge_id.wash_work_id.id)
                res = {
                    'domain': {'wash_type_id': [('id', 'in', wash_type_ids)]}
                }
            return res

    @api.model
    def create(self, vals):
        if 'dress_count_in' in vals:
            if vals['dress_count_in'] > 0:
                vals['laundry_track_code'] = self.env['ir.sequence'].next_by_code('laundry.line.sequence')
        result = super(SaleOrderLine, self).create(vals)
        return result

    @api.onchange('wash_type_id', 'product_uom_qty', 'other_than_wash_ids', 'dress_count_in')
    def wash_type_id_change(self):
        wash_charge = 0
        other_work_charge = 0
        for line in self:
            if line.wash_type_id:
                for wash_type_charge_id in self.product_id.washing_charge_ids:
                    if line.wash_type_id.id == wash_type_charge_id.wash_work_id.id and wash_type_charge_id.price:
                        wash_charge = wash_type_charge_id.price
            not_in = False
            if line.other_than_wash_ids:
                for other_than_wash_id in line.other_than_wash_ids:
                    for other_charge_id in self.product_id.other_charge_ids:
                        if other_than_wash_id.name == other_charge_id.other_work_id.name and other_charge_id.price:
                            other_work_charge += other_charge_id.price
                        else:
                            not_in = True
                    if not_in:
                        other_work_charge += other_than_wash_id.work_charge
                        not_in = False
            if wash_charge == 0 and line.wash_type_id:
                wash_charge = line.wash_type_id.washing_charge
            if line.other_than_wash_ids and other_work_charge == 0:
                for other_than_wash_id in line.other_than_wash_ids:
                    other_work_charge += other_than_wash_id.work_charge
            line.product_uom_qty = line.dress_count_in
            line.price_unit = wash_charge + other_work_charge

    def get_wash_type_charge(self, wash_type_id, product_id):
        product = self.env['product.product'].browse(product_id)
        for wash_type in product.washing_charge_ids:
            if wash_type.wash_work_id.id == wash_type_id:

                return wash_type.price
        return self.env['em.laundry.mgt.wash.type'].browse(wash_type_id).washing_charge

    def get_other_than_wash_charge(self, other_than_wash_id, product_id):
        product = self.env['product.product'].browse(product_id)
        # for other_charge_id in other_than_wash_ids:
        for other_charge in product.other_charge_ids:
            if other_than_wash_id == other_charge.other_work_id.id:
                return other_charge.price
        return self.env['em.laundry.other.than.wash'].browse(other_than_wash_id).work_charge


class AccountMoveExtended(models.Model):
    _inherit = "account.move"

    is_laundry_invoice = fields.Boolean()


class AccountMoveLineExtend(models.Model):
    _inherit = "account.move.line"

    wash_type_id = fields.Many2one('em.laundry.mgt.wash.type', string='Wash Type')
    other_than_wash_ids = fields.Many2many('em.laundry.other.than.wash', string='Other Than Wash')

    def get_wash_type_charge(self, wash_type_id, product_id):
        product = self.env['product.product'].browse(product_id)
        for wash_type in product.washing_charge_ids:
            if wash_type.wash_work_id.id == wash_type_id:

                return wash_type.price
        return self.env['em.laundry.mgt.wash.type'].browse(wash_type_id).washing_charge

    def get_other_than_wash_charge(self, other_than_wash_id, product_id):
        product = self.env['product.product'].browse(product_id)
        for other_charge in product.other_charge_ids:
            if other_than_wash_id == other_charge.other_work_id.id:
                return other_charge.price
        return self.env['em.laundry.other.than.wash'].browse(other_than_wash_id).work_charge


class ClothWashingCharges(models.Model):
    _name = "em.laundry.mgt.washing.charges"

    wash_work_id = fields.Many2one('em.laundry.mgt.wash.type', string='Washing')
    price = fields.Float('Charges')
    product_id = fields.Many2one('product.product')

    @api.onchange('wash_work_id')
    def wash_work_change(self):
        if self.wash_work_id:
            self.price = self.wash_work_id.washing_charge


class OtherThanWashingCharges(models.Model):
    _name = "em.laundry.mgt.other.charges"

    other_work_id = fields.Many2one('em.laundry.other.than.wash', string='Other Than Washing')
    price = fields.Float('Charges')
    product_id = fields.Many2one('product.product')

    @api.onchange('other_work_id')
    def other_work_change(self):
        if self.other_work_id:
            self.price = self.other_work_id.work_charge


class ProductProductExtend(models.Model):
    _inherit = "product.product"

    is_wash_type_clothe = fields.Boolean()
    washing_charge_ids = fields.One2many('em.laundry.mgt.washing.charges', 'product_id')
    other_charge_ids = fields.One2many('em.laundry.mgt.other.charges', 'product_id')
