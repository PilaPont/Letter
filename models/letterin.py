from datetime import datetime
import random

from odoo import models, fields, api, exceptions, _


class LetterIn(models.Model):
    _inherits = {'letter.letter': 'letter_id'}
    _name = 'letter.letter.in'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'Letter In'

    letter_id = fields.Many2one('letter.letter', ondelete="cascade")
    sender_letter_number = fields.Char(string='Sender Letter Number')
    receipt_date = fields.Date(string='Receipt Date', required=True)
    deadline_date = fields.Date(string='Response Deadline')

    state = fields.Selection([
        ('new', 'New'),
        ('registered', 'Registered'),
        ('returned', 'Returned'),
        ('assigned', 'Assigned'),
        ('done', 'Done')
            ], readonly=True, default='new', track_visibility='onchange')

    media_type = fields.Selection([
        ('fax', 'Fax'),
        ('email', 'E-mail'),
        ('p_email', 'Personal E-mail'),
        ('w_email', 'Working E-mail'),
        ('delivery', 'Delivery Man'),
        ('post', 'Post'),
        ('in_person', 'In person'),
        ('network', 'Social Networks')], required=True)

    email_id = fields.Many2one('res.users', string='Personal E_mail')
    is_current_user = fields.Boolean(compute='_compute_check_user', store=False)

    def _compute_check_user(self):
        self.is_current_user = self.user_id.id == self.env.uid
        return self.is_current_user

    @api.multi
    def write(self, values):
        if values.get('user_id'):
            self.activity(values)
        return super(LetterIn, self).write(values)

    @api.multi
    def register_button(self):
        for letter in self:
            if 'company_id' in self and (not letter.name):
                letter.name = self.env['ir.sequence'].with_context(
                    force_company=letter.company_id.id).next_by_code('letter.letter.in')
            else:
                letter.name = self.env['ir.sequence'].next_by_code('letter.letter.in')

            secretariat = list(self.env.ref('letter.group_access_secretariat').users.ids)

            user = random.choice(secretariat)
            letter.write({'state': 'registered', 'user_id': user})

    @api.multi
    def assign_button(self):
        return {
            'name': 'Assign Letter',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'letter.assign_letter_wizard',
            'context': {'default_letter_id': self.id}
        }

    @api.multi
    def return_button(self):
        for letter in self:
            secretariat = list(self.env.ref('letter.group_access_secretariat').users.ids)
            if self._uid in secretariat:
                letter.write({'state': 'returned', 'user_id': self._uid})
            else:
                user = random.choice(secretariat)
                letter.write({'state': 'returned', 'user_id': user})

    @api.multi
    def done_button(self):
        for letter in self:
            if self.user_id.id == self.env.uid:
                letter.write({'state': 'done'})
            else:
                raise exceptions.except_orm('Access Denied', 'only the responsible one can do it.')

    @api.multi
    def answer_button(self):
        return {
            'name': 'Answer to Letter In',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'letter.letter.out',
            'context': {'default_reference_type': 'reply_to',
                        'default_reference_letter_id': self.letter_id.id,
                        'default_partner_id': self.partner_id.id,
                        'default_user_id': self._uid,
                        'default_type': 'out',
                        }, }

    @api.onchange('reference_type')
    def _onchange_reference_type(self):
        self.reference_letter_type = 'in' if self.reference_type == 'following' else 'out'
        if self.reference_type == 'new':
            self.reference_letter_id = None

    def activity(self, values):
        self.activity_schedule(
            'letter.mail_activity_letter',
            user_id=values.get('user_id'),
            note="The send letter Assign to ")

    @api.multi
    def name_get(self):
        res = []
        for letter in self:
            name = letter.name
            if letter.partner_id.name and letter.subject:
                name = '%s - %s - %s' % (name, letter.partner_id.name, letter.subject)
            res.append((letter.id, name))
        return res
