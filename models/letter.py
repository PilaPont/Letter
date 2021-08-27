from datetime import datetime, timedelta
import random
import base64
import re

from odoo.modules.module import get_module_resource
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools.pdf import watermark_and_stamp_pdf


class Letter(models.Model):
    _name = 'letter.letter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Letter'

    STATES = ['draft', 'registered', 'returned', 'in_department', 'to_do',
              'sent', 'done', 'cancel', ]
    STATE_NAMES = ['New', 'Registered', 'Returned', 'Department Manager',
                   'To Do', 'Sent', 'Done', 'Canceled', ]
    DRAFT_STATES = ['draft', 'registered', 'returned', 'in_department', 'cancel', ]

    @api.model
    def default_get(self, fields_list):
        res = super(Letter, self).default_get(fields_list)
        if res.get('type') == 'in':
            res['send_receive_date'] = fields.Date.today()
        elif res.get('type') == 'out':
            res['layout_id'] = self.env['letter.layout'].search([('is_default', '=', True)], limit=1).id
        return res

    name = fields.Char(string="Letter Number", readonly=True, copy=False)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    cc_ids = fields.Many2many('res.partner', string='CC')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    content_id = fields.Many2one(comodel_name='letter.content_type', string='Content Type',
                                 required=True, tracking=True)
    date_deadline = fields.Datetime(string='Response Deadline', tracking=True,
                                    default=lambda *a: datetime.now().replace(second=0) + timedelta(days=2))
    delivery_method = fields.Selection([
        ('fax', 'Fax'),
        ('email', 'E-mail'),
        ('delivery', 'Delivery Man'),
        ('post', 'Post'),
        ('in_person', 'In person'),
        ('network', 'Social Networks')],
        readonly=True, states={'draft': [('readonly', False)]})
    font_size_title = fields.Char()
    font_size_signature = fields.Char()
    has_attachment = fields.Boolean(compute='_compute_has_attachment', store=True)
    is_current_user = fields.Boolean(compute='_compute_check_user', store=False)
    is_final = fields.Boolean(compute='_compute_is_final', store=True)
    layout_id = fields.Many2one('letter.layout', string='Letter Layout')
    letter_date = fields.Date()
    letter_text = fields.Html(string='Letter Text')
    meeting_id = fields.Many2one(comodel_name='calendar.event')
    messenger = fields.Char()
    partner_id = fields.Many2one(comodel_name='res.partner', required=True, tracking=True)
    phone_id = fields.Many2one('mail.activity',
                               domain=lambda self: ['|', ('activity_type_id.category', '=', 'phonecall'),
                                                    ('activity_type_id', '=',
                                                     self.env.ref('mail.mail_activity_data_call').id)],
                               string='Phone Call')
    reference_letter_id = fields.Many2one(comodel_name='letter.letter')
    reference_letter_type = fields.Char()
    reference_type = fields.Selection([
        ('draft', 'New Letter'),
        ('reply_to', 'In Reply To a Letter'),
        ('following', 'Following a Letter'),
        ('meeting', 'Following a Meeting'),
        ('phone', 'Following a Phone Call')], string='Reference', required=True, default='draft')
    related_letter_ids = fields.Many2many('letter.letter', string='Child letter', compute='_compute_related_letter_ids',
                                          store=False, copy=False)
    outgoing_mail_server_id = fields.Many2one(comodel_name='ir.mail_server', string='E-mail')
    print_preview = fields.Binary(compute='_compute_print_preview', store=True, attachment=True)
    send_receive_date = fields.Date(tracking=True)
    sender_letter_number = fields.Char(string='Sender Letter Number')
    signatory_id = fields.Many2one('res.users', string='Final Endorser',
                                   domain=lambda self: "[('groups_id','in',[" + str(
                                       self.env.ref('letter.group_can_sign_letter').id) + "])]", tracking=True)
    state = fields.Selection(list(zip(STATES, STATE_NAMES)), default='draft', readonly=True, tracking=True)
    subject = fields.Char(string='Subject', required=True, tracking=True)
    text_color = fields.Char()
    type = fields.Selection([('in', 'Incoming Letter'), ('out', 'Outgoing Letter')], required=True)
    use_signature_image = fields.Boolean(string='Print Signature', default=True)
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user, tracking=True)

    def _compute_check_user(self):
        self.is_current_user = self.user_id.id == self.env.uid

    @api.depends('attachment_ids')
    def _compute_has_attachment(self):
        for letter in self:
            letter.has_attachment = len(letter.attachment_ids) > 0

    @api.depends('state')
    def _compute_is_final(self):
        final_letters = self.filtered_domain([('state', 'not in', self.DRAFT_STATES)])
        final_letters.is_final = True
        (self - final_letters).is_final = False

    @api.depends('name', 'attachment_ids', 'cc_ids', 'company_id', 'has_attachment',
                 'layout_id', 'letter_date', 'letter_text', 'meeting_id', 'phone_id',
                 'reference_letter_id', 'reference_type', 'signatory_id', 'state',
                 'subject', 'use_signature_image')
    def _compute_print_preview(self):
        for letter in self:
            layout = letter.layout_id
            pdf, _dummy_ = self.env.ref('letter.action_report_letter')._render_qweb_pdf(letter.ids)

            if not letter.is_final:
                # todo: use dynamic stamp
                # find some way to render stamp, because of papersize mismatch
                stamp_file_path = get_module_resource('letter', 'static/pdf',
                                                      'preview-fa.pdf' if layout.language_id == self.env.ref(
                                                          'base.lang_fa_IR') else 'preview-en.pdf')
                stamp = open(stamp_file_path, 'rb').read()
            else:
                stamp = None

            watermark = base64.b64decode(layout.background_image) if layout.background_image else None

            letter.print_preview = base64.encodebytes(watermark_and_stamp_pdf(pdf, watermark, stamp))

    @api.depends('reference_letter_id')
    def _compute_related_letter_ids(self):
        for letter in self:
            letter.related_letter_ids = letter.reference_letter_id | letter.reference_letter_id.related_letter_ids

    @api.onchange('reference_type')
    def _onchange_reference_type(self):
        self.reference_letter_id = None
        if self.type == 'in':
            self.reference_letter_type = 'in' if self.reference_type == 'following' else 'out'
        elif self.type == 'out':
            self.reference_letter_type = 'out' if self.reference_type == 'following' else 'in'

    @api.model
    def create(self, values):
        if values.get('type') == 'out':
            content = values.get('letter_text')
            values['font_size_title'], values['font_size_signature'] = self._get_font_size(content)
            values['text_color'] = self._get_text_color(content)

        letter = super(Letter, self).create(values)
        if values.get('type') == 'out' and values.get('user_id'):
            letter._notify_user(values['user_id'])
        return letter

    def read(self, fields_list=None, load='_classic_read'):
        private_fields = ('letter_text', 'attachment_ids')

        if (self.env.user.has_group('letter.group_letter_see_all') or not any(
                field in fields_list for field in private_fields)):
            return super(Letter, self).read(fields=fields_list, load=load)
        else:
            extra_fields = []
            if fields_list and 'message_partner_ids' not in fields_list:
                extra_fields.append('message_partner_ids')

            data = super(Letter, self).read(fields=fields_list + extra_fields, load=load)
            invisible_letters = self._concealed_letter_ids(data)
            for record in invisible_letters:
                record['attachment_ids'] = []
                if self.type == 'out':
                    record['letter_text'] = _('You are not allowed to see letter content.')
            for record in data:
                if extra_fields:
                    for field in extra_fields:
                        del record[field]
            return data

    def write(self, values):
        for letter in self:
            if letter.type == 'out' and values.get('letter_text'):
                content = values.get('letter_text')
                letter['font_size_title'], letter['font_size_signature'] = letter._get_font_size(content)
                letter['text_color'] = letter._get_text_color(content)
        if values.get('reference_letter_id'):
            parent = self.env['letter.letter'].browse(values.get('reference_letter_id'))
            values['related_letter_ids'] = parent.related_letter_ids
        if values.get('user_id'):
            self._notify_user(values['user_id'])
        return super(Letter, self).write(values)

    ##################################

    def action_acknowledge(self):
        self.write({'state': 'done'})

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

    def action_assign(self):
        return {
            'name': 'Assign Letter',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'letter.assign_letter_wizard',
        }

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_done(self):
        for letter in self:
            if self.user_id.id == self.env.uid:
                letter.write({'state': 'done'})
            else:
                raise exceptions.ValidationError('Access Denied, only the responsible one can do it.')

    def action_draft(self):
        for letter in self:
            letter.write({'user_id': self.create_uid.id, 'state': 'draft'})

    def action_print(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/print_preview/{self.name}?download=true',
            'target': 'self',
        }

    def action_register(self):
        for letter in self:
            if 'company_id' in self and (not letter.name):
                letter.name = self.env['ir.sequence'].with_company(letter.company_id).next_by_code('letter.letter.in')
            else:
                letter.name = self.env['ir.sequence'].next_by_code('letter.letter.in')

            secretariat = list(self.env.ref('letter.group_access_secretariat').users.ids)
            if not secretariat:
                raise exceptions.UserError(_('At least one user should be set as secretary!'))
            user = random.choice(secretariat)
            letter.write({'state': 'registered', 'user_id': user})

    def action_reply(self):
        return {
            'name': 'Answer to Incoming Letter',
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

    def action_return(self):
        for letter in self:
            secretariat = list(self.env.ref('letter.group_access_secretariat').users.ids)
            if self._uid in secretariat:
                letter.write({'state': 'returned', 'user_id': self._uid})
            else:
                user = random.choice(secretariat)
                letter.write({'state': 'returned', 'user_id': user})

    def action_sent(self):
        """ change state and write field date  """
        user = self.user_id.id
        for letter in self:
            letter.send_receive_date = datetime.now().strftime(DATETIME_FORMAT)
            letter.write({'state': 'sent', 'user_id': user})

    def action_submit(self):
        """add letter number , change department user , change user to manager department """
        for letter in self:
            if 'company_id' in letter and (not letter.name):
                letter.name = letter.env['ir.sequence'].with_company(letter.company_id).next_by_code(
                    'letter.letter.out')
            else:
                letter.name = letter.env['ir.sequence'].next_by_code('letter.letter.out')
            if letter.user_id and letter.user_id != letter.signatory_id:
                letter.write({'user_id': letter.signatory_id.id, 'state': 'registered'})
            else:
                letter.write({'state': 'registered'})

    def name_get(self):
        res = []
        for letter in self:
            name = letter.name
            if letter.partner_id.name and letter.subject:
                name = '%s - %s - %s' % (name, letter.partner_id.name, letter.subject)
            res.append((letter.id, name))
        return res

    def _concealed_letter_ids(self, data):
        invisible_letters = []
        for record in data:
            if self.env.user.has_group('letter.group_letter_see_following') and self.env.user.partner_id.id not in \
                    record['message_partner_ids']:
                invisible_letters.append(record)
        return invisible_letters

    @staticmethod
    def _get_font_size(content):
        if re.findall('(?<=font-size:)\s?\d+.*?(?=;)', content):
            font_size_title = re.findall('(?<=font-size:)\s?\d+.*?(?=;)', content)[0].strip()
            font_size_signature = re.findall('(?<=font-size:)\s?\d+.*?(?=;)', content)[-1].strip()
        else:
            font_size_title, font_size_signature = '13px', '13px'
        return font_size_title, font_size_signature

    @staticmethod
    def _get_text_color(content):
        if re.findall('(?<=color:)\s?rgb\(\d+.*?(?=;)', content):
            text_color = re.findall('(?<=color:)\s?rgb\(\d+.*?(?=;)', content)[0].strip()
        else:
            text_color = '#2e3532'
        return text_color

    def _notify_user(self, user_id):
        self.activity_schedule('letter.mail_activity_letter', user_id=user_id)


class ContentType(models.Model):
    _name = 'letter.content_type'
    _description = 'Letter Content Type'

    name = fields.Char('Content', required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
