from odoo import models, fields


class AssignLetterWizard(models.TransientModel):
    _name = 'letter.assign_letter_wizard'
    _description = 'Letter Assign Wizard'

    letter_id = fields.Many2one(comodel_name='letter.letter',
                                domain=lambda self: [('type', '=', 'in')], required=True,
                                readonly=True)
    subject = fields.Char(related='letter_id.subject', string='Subject', readonly=True)
    user_id = fields.Many2one('res.users', string='Assignee', required=True)

    def do_save(self):
        letter = self.env['letter.letter'].browse(self.letter_id.id)  # (self.env.context.get('active_ids'))
        letter.write({'user_id': self.user_id.id, 'state': 'to_do'})
