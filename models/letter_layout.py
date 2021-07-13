from odoo import models, fields, api
from odoo.addons.base.models.report_paperformat import PAPER_SIZES


class LetterLayout(models.Model):
    _name = 'letter.layout'
    _description = 'Letter Layout'

    name = fields.Char()
    background_image = fields.Binary(string="Background Image", attachment=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    footer_height = fields.Integer('Footer Height (mm)')
    header_height = fields.Integer('Header Height (mm)')
    header_content_margin_right = fields.Integer('Header Content Margin Right (mm)')
    header_content_margin_top = fields.Integer('Header Content Margin Top (mm)')
    header_content_visible = fields.Boolean()
    is_default = fields.Boolean(string="Use as default")
    language_id = fields.Many2one('res.lang', string="language", required=True)
    margin_left = fields.Integer('Margin Left (mm)')
    margin_right = fields.Integer('Margin Right (mm)')
    page_height = fields.Integer('Page height (mm)', default=False)
    page_size = fields.Selection([(ps['key'], ps['description']) for ps in PAPER_SIZES], 'Paper size', default='A4',
                                 help="Select Proper Paper size")
    page_width = fields.Integer('Page width (mm)', default=False)

    @api.onchange('page_size')
    def _onchange_page_size(self):
        if self.page_size != 'custom':
            paper_size = next(ps for ps in PAPER_SIZES if ps['key'] == self.page_size)
            self.page_width = paper_size['width']
            self.page_height = paper_size['height']
