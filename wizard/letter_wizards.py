from odoo import models, fields


class AssignLetterWizard(models.TransientModel):
    _name = 'letter.assign_letter_wizard'
    _description = 'Letter Assign Wizard'

    letter_id = fields.Many2one(comodel_name='letter.letter',
                                default=lambda self: self._context.get('active_id'), required=True,
                                readonly=True)
    subject = fields.Char(related='letter_id.subject', string='Subject', readonly=True)
    user_id = fields.Many2one('res.users', string='Assignee', required=True)

    def do_save(self):
        self.letter_id.write({'user_id': self.user_id.id, 'state': 'to_do'})
