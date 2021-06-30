from odoo import models, fields, api
from odoo.addons.base.models.report_paperformat import PAPER_SIZES


class LetterLayout(models.Model):
    _name = 'letter.layout'
    _description = 'Letter Layout'
    # _inherits = {'report.paperformat': 'paperformat_id'}

    name = fields.Char()
    background_image = fields.Image(string="Background Image", attachment=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    footer_height = fields.Integer('Footer Height (mm)')
    footer_image = fields.Image(string="Footer Image", attachment=True)
    header_height = fields.Integer('Header Height (mm)')
    header_image = fields.Image(string="Header Image", attachment=True)
    is_default = fields.Boolean(string="Use as default")
    language_id = fields.Many2one('res.lang', string="language", required=True)
    layout_type = fields.Selection(selection=[('full', 'Full page'), ('split', 'Different header and Footer')],
                                   default='full')
    orientation = fields.Selection([('Landscape', 'Landscape'), ('Portrait', 'Portrait')], default='Landscape')
    page_height = fields.Integer('Page height (mm)', default=False)
    page_size = fields.Selection([(ps['key'], ps['description']) for ps in PAPER_SIZES], 'Paper size', default='A4',
                                 help="Select Proper Paper size")
    page_width = fields.Integer('Page width (mm)', default=False)
    text_start = fields.Integer('Start text from top (mm)')

    @api.onchange('page_size')
    def _onchange_page_size(self):
        if self.page_size != 'custom':
            paper_size = next(ps for ps in PAPER_SIZES if ps['key'] == self.page_size)
            self.page_width = paper_size['width']
            self.page_height = paper_size['height']
