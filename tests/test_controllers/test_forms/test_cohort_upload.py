# -*- coding:utf-8 -*-
import unittest
from nose.tools import assert_equal, raises, assert_true, assert_false, assert_raises
from exceptions import StopIteration

from tests.fixtures import WebTest
from wikimetrics.controllers.forms.cohort_upload import (
    parse_records,
    parse_username,
    normalize_newlines,
    parse_textarea_usernames,
)


class CohortsControllerTest(unittest.TestCase):
    
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
            'blahblahblahnor',
            'blahblah1\rblahblah2',
        ]
        lines = list(normalize_newlines(stream))
        assert_equal(len(lines), 5)
        assert_equal(lines[0], 'blahblah')
        assert_equal(lines[1], '')
        assert_equal(lines[2], 'blahblahblahnor')
        assert_equal(lines[3], 'blahblah1')
        assert_equal(lines[4], 'blahblah2')

    def test_parse_textarea_usernames(self):
        unparsed = """
                   dan,en\r
                   v\n
                   ,\r\n
                   """
        parsed = parse_textarea_usernames(unparsed)
        assert_equal(parsed.next(), ['dan', 'en'])
        assert_equal(parsed.next(), ['v'])
        assert_equal(parsed.next(), ['', ''])
        assert_raises(StopIteration, parsed.next)

    def test_parse_records_with_project(self):
        parsed = parse_records(
            [
                ['dan', 'wiki'],
                ['v', 'wiki'],
                [',', 'wiki']
            ],
            None
        )
        assert_equal(len(parsed), 3)
        assert_equal(parsed[0]['username'], 'Dan')
        assert_equal(parsed[0]['project'], 'wiki')
        assert_equal(parsed[1]['username'], 'V')
        assert_equal(parsed[1]['project'], 'wiki')
    
    def test_parse_records_without_project(self):
        parsed = parse_records(
            [
                ['dan'],
                ['v']
            ],
            'wiki'
        )
        assert_equal(len(parsed), 2)
        assert_equal(parsed[0]['username'], 'Dan')
        assert_equal(parsed[0]['project'], 'wiki')
        assert_equal(parsed[1]['username'], 'V')
        assert_equal(parsed[1]['project'], 'wiki')
    
    def test_parse_records_with_shorthand_project(self):
        parsed = parse_records(
            [
                ['dan', 'en']
            ],
            None
        )
        assert_equal(len(parsed), 1)
        assert_equal(parsed[0]['username'], 'Dan')
        assert_equal(parsed[0]['project'], 'en')
    
    def test_parse_records_with_utf8(self):
        parsed = parse_records(
            [
                [u'dan', 'en']
            ],
            None
        )
        assert_equal(len(parsed), 1)
        assert_equal(parsed[0]['username'], 'Dan')
        assert_equal(parsed[0]['project'], 'en')
