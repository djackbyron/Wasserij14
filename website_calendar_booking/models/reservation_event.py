# -*- coding: utf-8 -*-
from openerp.http import request

from openerp import api, fields, models,_
from odoo.exceptions import UserError

class ReservationEvent(models.Model):
    _name = 'reservation.event'

    name = fields.Char("Name")
    booking_email = fields.Char("Email")
    phone = fields.Char("Phone")
    pax = fields.Selection([('1','1'),
                            ('2', '2'),
                            ('3', '3'),
                            ('4', '4'),
                            ('5', '5'),
                            ('6', '6'),
                            ('morethan6', 'More than 6')
                            ],string="PAX")
    description = fields.Text("Special Occassion")
    start = fields.Datetime("Date")
    stop_time = fields.Datetime("Date")
    stop = fields.Datetime("Date")
    duration = fields.Float("Duration")
    type = fields.Char("Type")
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    partner_ids = fields.Many2one('res.partner',string="Responsible")
    code = fields.Char("Code")
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),('reject','Rejected')],string='State',track_visibility='onchange', default='draft', copy=False)

    def button_validate_action(self):
        self.state = 'confirm'

    def button_reject_action(self):
        self.state = 'reject'

    def button_reset_action(self):
        self.state = 'draft'

    def button_sendMail_action(self):
        pass

    def unlink(self):
        for move in self:
            if move.state != 'draft':
                raise UserError(_("You cannot delete an entry which has been confirmed or rejected."))
            move.unlink()
        return super(ReservationEvent, self).unlink()