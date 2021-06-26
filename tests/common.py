from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLetter(TransactionCase):
    print('Outgoing Letter test')

    def setUp(self):
        super(TestLetter, self).setUp()
        self.Letter_out = self.env['letter.letter']
        self.ResUser = self.env['res.users']
        self.Partner = self.env['res.partner']
        self.Content = self.env['letter.content_type']
        self.Header = self.env['letter.layout']

        self.create_header = self.Header.create({
            'name': 'template',
            'language_id': 1,
        })

        self.create_partner = self.Partner.create({
            'name': 'test',
        })

        self.create_content = self.Content.create({
            'name': 'letter',
        })

        self.Create_lo = self.Letter_out.create({
            'type': 'out',
            'subject': 'Outgoing Letter test',
            'partner_id': self.create_partner.id,
            'reference_type': 'new',
            'media_type': 'fax',
            'signatory_id': 1,
            'content_id': self.create_content.id,
            'layout_id': self.create_header.id,
            'state': 'draft',

        })

        # self.responsible = self.ResUser.create({
        #     'name': 'Repair Manager',
        #     'login': '12345',
        #     'email': 'admintest@yahoo.com',
        #     # 'groups_id': [(6, 0, [self.env.ref('letter.group_letter_out_see_all').id])],
        # })
