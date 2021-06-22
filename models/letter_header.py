from odoo import models, fields


class Header(models.Model):
    _name = 'letter.header'
    _description = 'Letter Header'
    # _inherits = {'report.paperformat': 'paperformat_id'}

    header_type = fields.Selection(selection=[('full', 'Full page'), ('split', 'Different header and Footer')])
    header_img = fields.Image(string="Header Image", attachment=True)
    footer_img = fields.Image(string="Footer Image", attachment=True)
    watermark = fields.Image(string="Footer Image", attachment=True)
    language_id = fields.Many2one('res.lang', string="language", required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    paperformat_id = fields.Many2one(comodel_name='report.paperformat', delegate=True)


