from datetime import datetime
import random

from odoo import models, fields, api, _, exceptions
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class LetterOut(models.Model):
    _inherits = {'letter.letter': 'letter_id'}
    _name = 'letter.letter.out'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Letter Out'

    letter_id = fields.Many2one('letter.letter', required=True, ondelete="cascade")
    signatory_id = fields.Many2one('res.users', string='Final Endorser',
                                   domain=lambda self: "[('groups_id','in',[" + str(
                                       self.env.ref('letter.group_can_sign_letter').id) + "])]", required=True,
                                   track_visibility='onchange')

    is_digital_signature = fields.Boolean(string='Digital Signature', default=True)
    letter_text = fields.Html(string='Letter Text')

    cc_ids = fields.Many2many('res.partner', string='CC')
    header_id = fields.Many2one('letter.header', string='Letter Header', required=True)
    letter_format_id = fields.Many2one('letter.format', string=' Letter Format', required=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('canceled', 'Canceled')], default='draft', readonly=True, track_visibility='onchange')

    media_type = fields.Selection([
        ('fax', 'Fax'),
        ('email', 'E-mail'),
        ('delivery', 'Delivery Man'),
        ('post', 'Post'),
        ('in_person', 'In person'),
        ('network', 'Social Networks')], required=True)

    is_current_user = fields.Boolean(compute='_compute_check_active_user', store=False)
    has_attachment = fields.Boolean(compute='_compute_has_attachment')

    def name_get(self):
        res = []
        for letter in self:
            name = letter.name
            if letter.partner_id.name and letter.subject:
                name = '%s - %s - %s' % (name, letter.partner_id.name, letter.subject)
            res.append((letter.id, name))
        return res

    @api.model
    def default_get(self, fields):
        res = super(LetterOut, self).default_get(fields)
        letter_format = self.env['letter.format'].search([('is_default', '=', True)])
        res['letter_format_id'] = letter_format[0].id if len(letter_format) > 0 else False
        res['type'] = 'out'
        return res

    def _compute_check_active_user(self):
        self.is_current_user = self.user_id.id == self.env.uid
        return self.is_current_user

    def action_draft(self):
        for letter in self:
            letter.write({'user_id': self.create_uid.id, 'state': 'draft'})
        # self.push_notification('DRAFTED','this is a notification')

    def action_submit(self):
        """add letter number , change department user , change user to manager department """
        for letter in self:
            if 'company_id' in letter and (not letter.name):
                letter.name = letter.env['ir.sequence'].with_context(
                    force_company=letter.company_id.id).next_by_code('letter.letter.out')
            else:
                letter.name = letter.env['ir.sequence'].next_by_code('letter.letter.out')
            if letter.user_id and letter.user_id != letter.signatory_id:
                letter.write({'user_id': letter.signatory_id.id, 'state': 'submitted'})
            else:
                letter.write({'state': 'submitted'})

    def action_approve(self):
        if list(self.env.ref('letter.group_access_secretariat').users.ids):
            secretariat = list(self.env.ref('letter.group_access_secretariat').users.ids)
            secretary = random.choice(secretariat)
            for letter in self:
                letter.issue_date = datetime.now().strftime(DATETIME_FORMAT)
                if self.user_id and self.user_id != secretary:
                    letter.write({'user_id': secretary, 'state': 'approved'})
                else:
                    letter.write({'state': 'approved'})

        else:
            raise exceptions.ValidationError('No secretary has defined!')

    def action_sent(self):
        """ change state and write field date  """
        user = self.user_id.id
        for letter in self:
            letter.send_date = datetime.now().strftime(DATETIME_FORMAT)
            letter.write({'state': 'sent', 'user_id': user})

    def action_acknowledge(self):
        self.write({'state': 'acknowledged'})

    def action_cancel(self):
        self.write({'state': 'canceled'})

    def activity(self, values, summery):
        """use model letter.mail_activity_letter for alert letter
        :param values:user_id
        :param summery
        """
        if (self.user_id.id == self.env.uid) and self.state == 'draft' and self.user == 1:
            self.user = 0
        else:
            self.activity_schedule(
                'letter.mail_activity_letter',
                user_id=values.get('user_id'),
                summary=summery, )

    @api.model
    def create(self, vals):
        record = super(LetterOut, self).create(vals)
        if vals.get('user_id'):
            record.activity(vals, 'New letter has created')
        return record

    def write(self, values):
        """
        :param values: default values
        :return: write information in database
        """
        if values.get('user_id'):
            self.activity(values, 'Letter responsible is changed')
        return super(LetterOut, self).write(values)

    def check_state(self):
        if self.state in ['approved', 'sent', 'acknowledged']:
            return True
        return False

    def _compute_has_attachment(self):
        for letter in self:
            letter.has_attachment = len(letter.attachment_ids) > 0

    @api.onchange('reference_type')
    def _onchange_reference_type(self):
        self.reference_letter_type = 'out' if self.reference_type == 'following' else 'in'

        if self.reference_type == 'new':
            self.reference_letter_id = None

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        PRIVATEFIELDS = ('letter_text', 'attachment_ids')
        if self.env.user.has_group('letter.group_letter_out_see_all') or not any(
                field in fields for field in PRIVATEFIELDS):
            return super(LetterOut, self).read(fields=fields, load=load)
        else:
            extra_fields = []
            if fields and 'message_partner_ids' not in fields:
                extra_fields.append('message_partner_ids')

            data = super(LetterOut, self).read(fields=fields + extra_fields, load=load)
            for record in data:
                if self.env.user.partner_id.id not in record['message_partner_ids']:
                    record['letter_text'] = _('You are not allowed to see letter content.')
                    record['attachment_ids'] = []
                if extra_fields:
                    for field in extra_fields:
                        del record[field]
            return data
