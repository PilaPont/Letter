from datetime import datetime
import random

from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class Letter(models.Model):
    _name = 'letter.letter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Letter'

    name = fields.Char(string="Letter Number", readonly=True, copy=False)
    type = fields.Selection([('in', 'Letter In'), ('out', 'Letter Out')], required=True, readonly=True)
    subject = fields.Char(string='Subject', required=True, tracking=True)
    partner_id = fields.Many2one(comodel_name='res.partner', required=True, tracking=True)
    letter_date = fields.Date()
    send_receive_date = fields.Date(tracking=True)
    content_id = fields.Many2one(comodel_name='letter.content_type', string='Content Type',
                                 required=True, tracking=True)
    reference_type = fields.Selection([
        ('draft', 'New Letter'),
        ('reply_to', 'In Reply To a Letter'),
        ('following', 'Following a Letter'),
        ('meeting', 'Following a Meeting'),
        ('phone', 'Following a Phone Call')], string='Reference', required=True, default='draft')

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user, tracking=True)

    role_based_email = fields.Many2one(comodel_name='ir.mail_server', string='E-mail')

    reference_letter_id = fields.Many2one(comodel_name='letter.letter')
    reference_letter_type = fields.Char()

    phone_id = fields.Many2one('mail.activity',
                               domain=lambda self: ['|', ('activity_type_id.category', '=', 'phonecall'),
                                                    ('activity_type_id', '=',
                                                     self.env.ref('mail.mail_activity_data_call').id)],
                               string='Phone Call')
    meeting_id = fields.Many2one('mail.activity',
                                 domain=lambda self: ['|',
                                                      ('activity_type_id.category', '=', 'meeting'),
                                                      ('activity_type_id', '=', self.env.ref(
                                                          'mail.mail_activity_data_meeting').id)],
                                 string='Meeting')

    related_letter_ids = fields.Many2many('letter.letter', string='Child letter', compute='_get_related_letter',
                                          store=False, copy=False)
    series = fields.Integer('Series', copy=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

    sender_letter_number = fields.Char(string='Sender Letter Number')
    deadline_date = fields.Date(string='Response Deadline')
    state = fields.Selection([
        ('draft', 'New'),
        ('registered', 'Registered'),
        ('returned', 'Returned'),
        ('in_department', 'Department Manager'),
        ('to_do', 'To Do'),
        ('sent', 'Sent'),
        ('done', 'Done'),
        ('canceled', 'Canceled')],
        default='draft', readonly=True, tracking=True)
    media_type = fields.Selection([
        ('fax', 'Fax'),
        ('email', 'E-mail'),
        ('delivery', 'Delivery Man'),
        ('post', 'Post'),
        ('in_person', 'In person'),
        ('network', 'Social Networks')])
    is_current_user = fields.Boolean(compute='_compute_check_user', store=False)

    signatory_id = fields.Many2one('res.users', string='Final Endorser',
                                   domain=lambda self: "[('groups_id','in',[" + str(
                                       self.env.ref('letter.group_can_sign_letter').id) + "])]", tracking=True)
    is_digital_signature = fields.Boolean(string='Digital Signature', default=True)
    letter_text = fields.Html(string='Letter Text')
    cc_ids = fields.Many2many('res.partner', string='CC')
    header_id = fields.Many2one('letter.header', string='Letter Header')
    letter_format_id = fields.Many2one('letter.format', string='Letter Format',
                                       default=lambda self: self.env.ref('letter.normal_format'))
    has_attachment = fields.Boolean(compute='_compute_has_attachment')

    @api.model
    def create(self, values):
        if values.get('reference_letter_id'):
            parent = self.env['letter.letter'].browse(values.get('reference_letter_id'))
            values['series'] = parent.series
            letter = super(Letter, self).create(values)
        else:
            letter = super(Letter, self).create(values)
            letter.series = letter.id
        if values.get('type') == 'out' and values.get('user_id'):
            letter.activity(values)
        return letter

    def write(self, values):
        if values.get('reference_letter_id'):
            parent = self.env['letter.letter'].browse(values.get('reference_letter_id'))
            values['series'] = parent.series
        if values.get('user_id'):
            self.activity(values)
        return super(Letter, self).write(values)

    def activity(self, values):
        self.activity_schedule(
            'letter.mail_activity_letter',
            user_id=values.get('user_id'))

    @api.depends('series')
    def _get_related_letter(self):
        for letter in self:
            children = self.env['letter.letter'].search([('series', '=', letter.series)])
            for child in children:
                letter.related_letter_ids += child

    ###############################
    @api.model
    def default_get(self, fields):
        res = super(Letter, self).default_get(fields)
        if self.type == 'in':
            res['type'] = 'in'
        elif self.type == 'out':
            letter_format = self.env['letter.format'].search([('is_default', '=', True)])
            res['letter_format_id'] = letter_format[0].id if len(letter_format) > 0 else False
            res['type'] = 'out'
        return res

    def _compute_check_user(self):
        self.is_current_user = self.user_id.id == self.env.uid
        return self.is_current_user

    def register_button(self):
        for letter in self:
            if 'company_id' in self and (not letter.name):
                letter.name = self.env['ir.sequence'].with_context(
                    force_company=letter.company_id.id).next_by_code('letter.letter.in')
            else:
                letter.name = self.env['ir.sequence'].next_by_code('letter.letter.in')

            secretariat = list(self.env.ref('letter.group_access_secretariat').users.ids)
            if not secretariat:
                raise exceptions.UserError(_('At least one user should be set as secretary!'))
            user = random.choice(secretariat)
            letter.write({'state': 'registered', 'user_id': user})

    def assign_button(self):
        return {
            'name': 'Assign Letter',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'letter.assign_letter_wizard',
        }

    def return_button(self):
        for letter in self:
            secretariat = list(self.env.ref('letter.group_access_secretariat').users.ids)
            if self._uid in secretariat:
                letter.write({'state': 'returned', 'user_id': self._uid})
            else:
                user = random.choice(secretariat)
                letter.write({'state': 'returned', 'user_id': user})

    def done_button(self):
        for letter in self:
            if self.user_id.id == self.env.uid:
                letter.write({'state': 'done'})
            else:
                raise exceptions.ValidationError('Access Denied, only the responsible one can do it.')

    def answer_button(self):
        return {
            'name': 'Answer to Letter In',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'letter.letter',
            'context': {'default_reference_type': 'reply_to',
                        'default_reference_letter_id': self.id,
                        'default_partner_id': self.partner_id.id,
                        'default_user_id': self._uid,
                        'default_type': 'out',
                        }, }

    @api.onchange('reference_type')
    def _onchange_reference_type(self):
        if self.type == 'in':
            self.reference_letter_type = 'in' if self.reference_type == 'following' else 'out'
        elif self.type == 'out':
            self.reference_letter_type = 'out' if self.reference_type == 'following' else 'in'

        if self.reference_type == 'new':
            self.reference_letter_id = None

    def name_get(self):
        res = []
        for letter in self:
            name = letter.name
            if letter.partner_id.name and letter.subject:
                name = '%s - %s - %s' % (name, letter.partner_id.name, letter.subject)
            res.append((letter.id, name))
        return res

    ##################################

    def action_draft(self):
        for letter in self:
            letter.write({'user_id': self.create_uid.id, 'state': 'draft'})

    def action_submit(self):
        """add letter number , change department user , change user to manager department """
        for letter in self:
            if 'company_id' in letter and (not letter.name):
                letter.name = letter.env['ir.sequence'].with_context(
                    force_company=letter.company_id.id).next_by_code('letter.letter.out')
            else:
                letter.name = letter.env['ir.sequence'].next_by_code('letter.letter.out')
            if letter.user_id and letter.user_id != letter.signatory_id:
                letter.write({'user_id': letter.signatory_id.id, 'state': 'registered'})
            else:
                letter.write({'state': 'registered'})

    def action_approve(self):
        if list(self.env.ref('letter.group_access_secretariat').users.ids):
            secretariat = list(self.env.ref('letter.group_access_secretariat').users.ids)
            if not secretariat:
                raise exceptions.UserError(_('At least one user should be set as secretary!'))
            secretary = random.choice(secretariat)
            for letter in self:
                letter.letter_date = datetime.now().strftime(DATETIME_FORMAT)
                if self.user_id and self.user_id.id != secretary:
                    letter.write({'user_id': secretary, 'state': 'to_do'})
                else:
                    letter.write({'state': 'to_do'})

        else:
            raise exceptions.ValidationError(_('No secretary has defined!'))

    def action_sent(self):
        """ change state and write field date  """
        user = self.user_id.id
        for letter in self:
            letter.send_receive_date = datetime.now().strftime(DATETIME_FORMAT)
            letter.write({'state': 'sent', 'user_id': user})

    def action_acknowledge(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'canceled'})

    def check_state(self):
        if self.state in ['to_do', 'sent', 'done']:
            return True
        return False

    def _compute_has_attachment(self):
        for letter in self:
            letter.has_attachment = len(letter.attachment_ids) > 0

    def read(self, fields=None, load='_classic_read'):
        PRIVATEFIELDS = ('letter_text', 'attachment_ids')

        if (self.env.user.has_group('letter.group_letter_see_all') or not any(
                field in fields for field in PRIVATEFIELDS)):
            return super(Letter, self).read(fields=fields, load=load)
        else:
            extra_fields = []
            if fields and 'message_partner_ids' not in fields:
                extra_fields.append('message_partner_ids')

            data = super(Letter, self).read(fields=fields + extra_fields, load=load)
            invisible_letters = self.concealed_letter_ids(data)
            for record in invisible_letters:
                record['attachment_ids'] = []
                if self.type == 'out':
                    record['letter_text'] = _('You are not allowed to see letter content.')
            for record in data:
                if extra_fields:
                    for field in extra_fields:
                        del record[field]
            return data

    def concealed_letter_ids(self, data):
        invisible_letters = []
        for record in data:
            if self.env.user.has_group('letter.group_letter_see_follower') and self.env.user.partner_id.id not in \
                    record['message_partner_ids']:
                invisible_letters.append(record)
        return invisible_letters

    def print_letter(self):
        return self.env.ref('letter.report_letter_out').report_action(self)
