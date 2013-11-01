# -*- coding:utf-8 -*-
import datetime
import decimal
from nose.tools import assert_true, assert_equal
from unittest import TestCase
from wikimetrics.utils import (
    stringify,
    deduplicate_by_key,
    to_safe_json,
    project_name_for_link,
    link_to_user_page,
    parse_pretty_date,
    format_pretty_date,
)
from wikimetrics.metrics import NamespaceEdits


class UtilsTest(TestCase):
    
    def test_better_encoder_date(self):
        result = stringify(date_not_date_time=datetime.date(2013, 06, 01))
        assert_true(result.find('"date_not_date_time"') >= 0)
        assert_true(result.find('2013-06-01') >= 0)
    
    def test_better_encoder_datetime(self):
        result = stringify(date_time=datetime.datetime(2013, 06, 01, 02, 03, 04))
        assert_true(result.find('"date_time"') >= 0)
        assert_true(result.find('2013-06-01 02:03:04') >= 0)
    
    def test_better_encoder_decimal(self):
        result = stringify(deci=decimal.Decimal(6.01))
        assert_true(result.find('"deci"') >= 0)
        assert_true(result.find('6.01') >= 0)
    
    def test_better_encoder_default(self):
        result = stringify(normal='hello world')
        assert_true(result.find('"normal"') >= 0)
        assert_true(result.find('normal') >= 0)
    
    def test_deduplicate_by_key(self):
        collection_of_dicts = [
            {'index': 'one', 'other': '1'},
            {'index': 'two', 'other': '2'},
            {'index': 'two', 'other': '3'},
        ]
        no_duplicates = deduplicate_by_key(collection_of_dicts, lambda r: r['index'])
        expected = collection_of_dicts[0:2]
        assert_equal(sorted(no_duplicates), expected)
    
    def test_deduplicate_by_key_tuple(self):
        collection_of_dicts = [
            {'index': 'one', 'other': '1'},
            {'index': 'two', 'other': '2'},
            {'index': 'two', 'other': '3'},
            {'index': 'two', 'other': '2'},
        ]
        no_duplicates = deduplicate_by_key(
            collection_of_dicts,
            lambda r: (r['index'], r['other'])
        )
        expected = collection_of_dicts[0:3]
        assert_equal(sorted(no_duplicates), expected)
    
    def test_to_safe_json(self):
        unsafe_json = '{"quotes":"He''s said: \"Real Artists Ship.\""}'
        safe_json = to_safe_json(unsafe_json)
        
        assert_equal(
            safe_json,
            '\\"{\\\\"quotes\\\\":\\\\"Hes said: \\\\"Real Artists Ship.\\\\"\\\\"}\\"'
        )
    
    def test_project_name_for_link(self):
        project = project_name_for_link('en')
        assert_equal(project, 'en')
    
    def test_project_name_for_link_with_wiki(self):
        project = project_name_for_link('enwiki')
        assert_equal(project, 'en')
    
    def test_link_to_user_page(self):
        link = link_to_user_page('Dan has-spaces', 'en')
        assert_equal(link, 'https://en.wikipedia.org/wiki/User:Dan has-spaces')
    
    def test_link_to_user_page_unicode(self):
        link_to_user_page('ولاء عبد المنعم', 'ar')
        # just want to make sure no exceptions are raised
        assert_true(True)
    
    def test_parse_pretty_date(self):
        date = datetime.datetime(2012, 2, 3, 4, 5)
        assert_equal(date, parse_pretty_date(format_pretty_date(date)))
