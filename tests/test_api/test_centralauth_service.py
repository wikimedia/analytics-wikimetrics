# -*- coding: utf-8 -*-
from nose.tools import assert_equal, assert_true
from tests.fixtures import DatabaseTest
from wikimetrics.models.centralauth import CentralAuthLocalUser as LocalUser
from wikimetrics.api import CentralAuthService


class CentralAuthServiceTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.expand = CentralAuthService().expand_via_centralauth

    def test_expand_via_centralauth(self):
        username_1, username_2 = 'User 1', 'User 2'
        wiki_1, wiki_2, wiki_3 = 'wiki1', 'wiki2', 'wiki3'
        self.caSession.add_all([
            LocalUser(lu_name=username_1, lu_wiki=wiki_1),
            LocalUser(lu_name=username_1, lu_wiki=wiki_2),
            LocalUser(lu_name=username_1, lu_wiki=wiki_3),
            LocalUser(lu_name=username_2, lu_wiki=wiki_1),
            LocalUser(lu_name=username_2, lu_wiki=wiki_2),
        ])
        self.caSession.commit()

        records = self.expand(
            [{'raw_id_or_name': username_1, 'project': wiki_1}],
            self.caSession
        )
        assert_equal([
            {'raw_id_or_name': username_1, 'project': wiki_1},
            {'raw_id_or_name': username_1, 'project': wiki_2},
            {'raw_id_or_name': username_1, 'project': wiki_3},
        ], records)

        records = self.expand(
            [{'raw_id_or_name': username_2, 'project': wiki_1}],
            self.caSession
        )
        assert_equal([
            {'raw_id_or_name': username_2, 'project': wiki_1},
            {'raw_id_or_name': username_2, 'project': wiki_2},
        ], records)

        records = self.expand(
            [
                {'raw_id_or_name': username_1, 'project': wiki_1},
                {'raw_id_or_name': username_2, 'project': wiki_1},
            ],
            self.caSession
        )
        assert_equal(len(records), 5)

    def test_expand_user_without_centralauth(self):
        '''
        If a cohort user does not belong to centralauth localuser table
        it should not be filtered out by expand_via_centralauth
        or else the user won't receive the negative validation feedback.
        '''
        username, wiki = 'Non-existent', 'notimportant'
        records = self.expand(
            [{'raw_id_or_name': username, 'project': wiki}],
            self.caSession
        )
        assert_equal(len(records), 1)
        assert_equal(records[0]['raw_id_or_name'], username)

    def test_expand_utf8_user(self):
        '''
        expand_via_centralauth must support utf-8 user names.
        Note the encoding at the first line of this file.
        '''
        username = "ام محمود"
        wiki_1, wiki_2 = 'wiki1', 'wiki2'
        self.caSession.add_all([
            LocalUser(lu_name=username, lu_wiki=wiki_1),
            LocalUser(lu_name=username, lu_wiki=wiki_2),
        ])
        self.caSession.commit()
        records = self.expand(
            [{'raw_id_or_name': username, 'project': wiki_1}],
            self.caSession
        )
        assert_equal([
            {'raw_id_or_name': username, 'project': wiki_1},
            {'raw_id_or_name': username, 'project': wiki_2},
        ], records)

    def test_expand_user_without_duplicates(self):
        '''
        If a cohort has duplicate users
        there's no need to explode them all.
        '''
        username = 'User'
        wiki_1, wiki_2 = 'enwiki', 'hiwiki'
        self.caSession.add_all([
            LocalUser(lu_name=username, lu_wiki=wiki_1),
            LocalUser(lu_name=username, lu_wiki=wiki_2),
        ])
        self.caSession.commit()
        records = self.expand(
            [
                {'raw_id_or_name': username, 'project': wiki_1},
                {'raw_id_or_name': username, 'project': wiki_1},
            ],
            self.caSession
        )
        assert_equal([
            {'raw_id_or_name': username, 'project': wiki_1},
            {'raw_id_or_name': username, 'project': wiki_2},
        ], records)
