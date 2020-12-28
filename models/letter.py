from odoo import models, fields, api


class Letter(models.Model):
    _name = 'letter.letter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'A module to handle all sent and received letters/parcels/goods/catalogues/etc. in a company'

    name = fields.Char(string="Letter Number", readonly=True, copy=False)
    type = fields.Selection([('in', 'Letter In'), ('out', 'Letter Out')], required=True, readonly=True)
    subject = fields.Char(string='Subject', required=True, track_visibility='onchange')
    partner_id = fields.Many2one(comodel_name='res.partner', required=True, track_visibility='onchange')
    issue_date = fields.Date(string='Issue Date', default=None)
    send_date = fields.Date(string='Send Date', default=None, track_visibility='onchange')
    content_id = fields.Many2one(comodel_name='letter.content_type', string='Content Type',
                                 required=True, track_visibility='onchange')
    reference_type = fields.Selection([
        ('new', 'New Letter'),
        ('reply_to', 'In Reply To a Letter'),
        ('following', 'Following a Letter'),
        ('meeting', 'Following a Meeting'),
        ('phone', 'Following a Phone Call')], string='Reference', required=True, default=None)

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user, track_visibility='onchange')

    role_based_email = fields.Many2one(comodel_name='ir.mail_server', string='E-mail')

    reference_letter_id = fields.Many2one(comodel_name='letter.letter')
    reference_letter_type = fields.Char()

    phone_id = fields.Many2one('mail.activity', domain=lambda self: "[('activity_type_id','='," + str(
        self.env.ref('mail.mail_activity_data_call').id) + ")]", string='Phone Call')
    meeting_id = fields.Many2one('mail.activity', domain=lambda self: "[('activity_type_id','='," + str(
        self.env.ref('mail.mail_activity_data_meeting').id) + ")]", string='Meeting')

    related_letter_ids = fields.Many2many('letter.letter', string='Child letter', compute='_get_related_letter',
                                          store=False, copy=False)
    series = fields.Integer('Series', copy=False)
    user = fields.Integer()
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

    @api.model
    def create(self, values):
        if values.get('reference_letter_id'):
            parent = self.env['letter.letter'].browse(values.get('reference_letter_id'))
            values['series'] = parent.series
            letter = super(Letter, self).create(values)
        else:
            letter = super(Letter, self).create(values)
            letter.series = letter.id
        return letter

    def write(self, values):
        if values.get('reference_letter_id'):
            parent = self.env['letter.letter'].browse(values.get('reference_letter_id'))
            values['series'] = parent.series
        return super(Letter, self).write(values)

    @api.depends('series')
    def _get_related_letter(self):
        for letter in self:
            children = self.env['letter.letter'].search([('series', '=', letter.series)])
            for child in children:
                letter.related_letter_ids += child
