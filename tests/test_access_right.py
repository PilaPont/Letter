from odoo.exceptions import AccessError, UserError
from odoo.addons.letter.tests.common import TestLetter, tagged


@tagged('post_install', '-at_install')
class TestAccessRights(TestLetter):
    def setUp(self):
        super(TestAccessRights, self).setUp()

        Users = self.env['res.users'].with_context(no_reset_password=True)

        group_see_all = self.env.ref('letter.group_letter_out_see_all')
        group_follower = self.env.ref('letter.group_letter_out_see_follower')
        group_signature = self.env.ref('letter.group_can_sign_letter')
        group_secretariat = self.env.ref('letter.group_access_secretariat')
        group_config = self.env.ref('base.group_no_one')

        self.user_see_all = Users.create({
            'name': 'Alias Manager',
            'login': 'manager',
            'email': 'a.m@example.com',
            'groups_id': [(6, 0, [group_see_all.id])]
        })
        self.user_follower = Users.create({
            'name': 'Mark Follower',
            'login': 'user',
            'email': 'm.u@example.com',
            'groups_id': [(6, 0, [group_follower.id])]
        })
        self.user_signa = Users.create({
            'name': 'Nina Signature',
            'login': 'nina',
            'email': 'n.s@example.com',
            'groups_id': [(6, 0, [group_signature.id])]
        })
        self.user_secretariat = Users.create({
            'name': 'Chell Secret',
            'login': 'chell',
            'email': 'c.s@example.com',
            'groups_id': [(6, 0, [group_secretariat.id])]
        })
        self.user_config = Users.create({
            'name': 'Bert Config',
            'login': 'bert',
            'email': 'b.c@example.com',
            'groups_id': [(6, 0, [group_config.id])]
        })

        self.letter_out= self.Letter_out.with_context(tracking_disable=True).create({
            'type': 'out',
            'subject': 'Outgoing Letter test',
            'partner_id': self.create_partner.id,
            'reference_type': 'new',
            'media_type': 'fax',
            'signatory_id': 1,
            'content_id': self.create_content.id,
            'header_id': self.create_header.id,
            'state': 'draft',
        })

        self.content = self.Content.with_context(tracking_disable=True).create({
            'name': 'test1',
        })

        self.header = self.Header.create({
            'name': 'temp',
            'language_id': 2,
        })

    # def test_user_see_all(self):
    #     print('start see all')
    #     self.letter_out.with_user(self.user_see_all).read()
    #     print('ended see all')

    # def test_follower(self):
    #     print('start follower')
    #     self.letter_out.with_user(self.user_follower).read()
    #     self.letter_out.with_user(self.user_follower).write({
    #         'subject': 'test 11111',
    #     })
    #     print('ended follower')

    def test_user_config(self):
        print('start config user 111')

        with self.assertRaises(AccessError):
            self.content.with_user(self.user_signa).read()

        self.content.with_user(self.user_config).read()
        self.header.with_user(self.user_config).read()

        self.content.with_user(self.user_config).write({
            'name': 'testk',
        })

        self.header.with_user(self.user_config).write({
            'name': 'temp two',
            'language_id': 1,
        })
        with self.assertRaises(AccessError):
            self.header.with_user(self.user_signa).write({
                'name': 'temp two',
            })

        self.env['letter.content_type'].with_user(self.user_config).create({
            'name': 'test3',
        })
        with self.assertRaises(AccessError):
            self.env['letter.content_type'].with_user(self.user_see_all).create({
                'name': 'test3',
            })

        self.env['letter.header'].with_user(self.user_config).create({
            'name': 'header aria',
            'language_id': 1,
        })
        with self.assertRaises(AccessError):
            self.env['letter.header'].with_user(self.user_see_all).create({
                'name': 'header aria',
                'language_id': 1,
            })

        with self.assertRaises(AccessError):
            self.header.with_user(self.user_see_all).unlink()

        with self.assertRaises(AccessError):
            self.content.with_user(self.user_signa).unlink()

        self.content.with_user(self.user_config).unlink()
        self.header.with_user(self.user_config).unlink()

        print('ended config user 222')
