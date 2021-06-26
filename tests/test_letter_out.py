import os
import random
from datetime import datetime
from odoo.addons.letter.tests.common import TestLetter, tagged
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


@tagged('post_install', '-at_install')
class TestLetterOut(TestLetter):

    def test_create_content(self):
        print('Start create content')
        rec = self.env['letter.content_type'].create({'name': 'letter'})
        self.assertEqual(rec.name, 'letter')
        print('End create content')

    def test_action_submit(self):
        print('Start submit')
        letter_out = self.Letter_out.create({
            'type': 'out',
            'subject': 'Outgoing Letter test',
            'partner_id': self.create_partner.id,
            'reference_type': 'new',
            'media_type': 'fax',
            'signatory_id': 1,
            'content_id': self.create_content.id,
            'layout_id': self.create_header.id,
            'state': 'draft',
            'name': 'Lo-2020-00001'

        })
        letter_out.action_submit()
        self.assertEqual(letter_out.user_id.id, 1)
        print('End submit')

    def test_action_approve(self):
        print('Start approve')

        letter_out = self.Letter_out.create({
            'type': 'out',
            'subject': 'Outgoing Letter test',
            'partner_id': self.create_partner.id,
            'reference_type': 'new',
            'media_type': 'fax',
            'signatory_id': 1,
            'content_id': self.create_content.id,
            'layout_id': self.create_header.id,
            'state': 'registered',
            'name': 'Lo-2020-00001',
            'user_id': random.choice(list(self.env.ref('letter.group_access_secretariat').users.ids)),
            'letter_date': datetime.now().strftime(DATETIME_FORMAT),

        })
        print(list(self.env.ref('letter.group_access_secretariat').users.ids))

        letter_out.action_approve()
        self.assertEqual(letter_out.state, 'approved')
        self.assertEquals(str(letter_out.letter_date), datetime.now().strftime('%Y-%m-%d'))
        self.assertEqual(letter_out.user_id.id, 2)
        print('End action approve')

    def test_action_sent(self):
        print('Start sent')

        letter_out = self.Letter_out.create({
            'type': 'out',
            'subject': 'Outgoing Letter test',
            'partner_id': self.create_partner.id,
            'reference_type': 'new',
            'media_type': 'fax',
            'signatory_id': 1,
            'content_id': self.create_content.id,
            'layout_id': self.create_header.id,
            'state': 'approved',
            'name': 'Lo-2020-00001',
            'letter_date': '2020-01-27',
            'send_receive_date': datetime.now().strftime(DATETIME_FORMAT),
        })

        letter_out.action_sent()
        self.assertEqual(letter_out.state, 'sent')
        self.assertEquals(str(letter_out.send_receive_date), datetime.now().strftime('%Y-%m-%d'))

        print('End Send')

    def test_action_acknowledge(self):
        print('Start Acknowledge')

        letter_out = self.Letter_out.create({
            'type': 'out',
            'subject': 'Outgoing Letter test',
            'partner_id': self.create_partner.id,
            'reference_type': 'new',
            'media_type': 'fax',
            'signatory_id': 1,
            'content_id': self.create_content.id,
            'layout_id': self.create_header.id,
            'state': 'sent',
            'name': 'Lo-2020-00001',
            'letter_date': '2020-01-27',
            'send_receive_date': '2020-01-27',
        })

        letter_out.action_acknowledge()
        self.assertEqual(letter_out.state, 'acknowledged')
        print('End Acknowledge')

