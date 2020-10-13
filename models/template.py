# -*- coding: utf-8 -*-
from odoo import models, fields, api


class LetterFormat(models.Model):
    _name = 'letter.format'

    name = fields.Char(string="Compact Format Name", required=True, translate=True)
    font_size = fields.Integer(string='Font Size', required=True)
    is_default = fields.Boolean(string='Default')
    is_active = fields.Boolean(string='Active', default=True)


class Header(models.Model):
    _name = 'letter.header'

    name = fields.Char(string="Header Name", required=True, translate=True)
    header_img = fields.Binary(string="Header Image", attachment=True)
    footer_img = fields.Binary(string="Footer Image", attachment=True)
    language_id = fields.Many2one('res.lang', string="language", required=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)


class ContentType(models.Model):
    _name = 'letter.content_type'

    name = fields.Char('Content', required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
