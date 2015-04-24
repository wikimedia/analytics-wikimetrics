# -*- coding: utf-8 -*-
import unittest
from nose.tools import assert_equal, raises, assert_true, assert_false, assert_raises
from exceptions import StopIteration

from tests.fixtures import WebTest
from wikimetrics.forms.cohort_upload import (
    format_records,
    parse_username,
    normalize_newlines,
    parse_textarea_ids_or_names,
)


class CohortsControllerTest(unittest.TestCase):

    def test_parse_username_unicode_handling(self):
        unparsed_strings = [u'sès', u'مو', u'èm']
        expected_strings = ['S\xc3\xa8s', '\xd9\x85\xd9\x88', '\xc3\x88m']

        for unparsed, expected in zip(unparsed_strings, expected_strings):
            username = parse_username(unparsed)
            assert_equal(username, expected)

    def test_validate_username(self):
        # this username has a few problems that the normalize call should handle
        # 1. normal ascii space in front
        # 2. lowercase
        # 3. nasty trailing unicode space (the reason this file has coding:utf-8)
        problem_username = ' editor test-specific-0 '

        parsed_user = parse_username(problem_username)
        assert_equal(parsed_user, 'Editor test-specific-0')

    def test_normalize_newlines(self):
        stream = [
            'blahblah\r',
            'blahblahblah\r\n',
            'blahblahblahnormal',
            'blahblah1\rblahblah2',
        ]
        lines = list(normalize_newlines(stream))
        assert_equal(len(lines), 5)
        assert_equal(lines[0], 'blahblah')
        assert_equal(lines[1], 'blahblahblah')
        assert_equal(lines[2], 'blahblahblahnormal')
        assert_equal(lines[3], 'blahblah1')
        assert_equal(lines[4], 'blahblah2')

    def test_parse_textarea_ids_or_names(self):
        unparsed = 'dan,en\rv\n,\r\nsomething with spaces'
        parsed = parse_textarea_ids_or_names(unparsed)
        assert_equal(parsed[0], 'dan,en')
        assert_equal(parsed[1], 'v')
        assert_equal(parsed[2], ',')
        assert_equal(parsed[3], 'something with spaces')
        assert_equal(len(parsed), 4)
        # needs to deal with unicode types as that is what this
        # method will get from flask
        unparsed = u'تيسير سامى سلامة,en\rv\n,\r\nsomething with spaces'
        parsed = parse_textarea_ids_or_names(unparsed)
        username = parsed[0]
        # username will be just plain bytes, convert to unicode
        # to be able to compare
        assert_equal(username.decode("utf-8"), u'تيسير سامى سلامة,en')

    def test_format_records_with_project(self):
        parsed = format_records(
            [
                'dan,wiki',
                'v,wiki',
                ',,wiki',
            ],
            None
        )
        assert_equal(len(parsed), 3)
        assert_equal(parsed[0]['raw_id_or_name'], 'Dan')
        assert_equal(parsed[0]['project'], 'wiki')
        assert_equal(parsed[1]['raw_id_or_name'], 'V')
        assert_equal(parsed[1]['project'], 'wiki')

    def test_format_records_without_project(self):
        parsed = format_records(
            ['dan', 'v'],
            'wiki'
        )
        assert_equal(len(parsed), 2)
        assert_equal(parsed[0]['raw_id_or_name'], 'Dan')
        assert_equal(parsed[0]['project'], 'wiki')
        assert_equal(parsed[1]['raw_id_or_name'], 'V')
        assert_equal(parsed[1]['project'], 'wiki')

    def test_format_records_with_shorthand_project(self):
        parsed = format_records(
            ['dan,en'],
            None
        )
        assert_equal(len(parsed), 1)
        assert_equal(parsed[0]['raw_id_or_name'], 'Dan')
        assert_equal(parsed[0]['project'], 'en')

    def test_format_records_with_utf8(self):
        '''
        Format records deals with bytes but should be
        able to handle non ascii chars
        '''
        username = u'Kán'.encode("utf-8")
        parsed = format_records(
            [username + ',en'],
            None
        )
        assert_equal(len(parsed), 1)
        assert_equal(parsed[0]['raw_id_or_name'], u'Kán'.encode("utf-8"))
        assert_equal(parsed[0]['project'], 'en')

    def test_format_records_with_spaces_in_project(self):
        parsed = format_records(
            ['dan, en'],
            None
        )
        assert_equal(len(parsed), 1)
        assert_equal(parsed[0]['raw_id_or_name'], 'Dan')
        assert_equal(parsed[0]['project'], 'en')
