# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
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
    diff_datewise,
    timestamps_to_now,
    parse_tag,
    chunk,
    update_dict,
)
from wikimetrics.metrics import NamespaceEdits


class UtilsTest(TestCase):
    
    def test_better_encoder_date(self):
        result = stringify(date_not_date_time=date(2013, 06, 01))
        assert_true(result.find('"date_not_date_time"') >= 0)
        assert_true(result.find('2013-06-01') >= 0)
    
    def test_better_encoder_datetime(self):
        result = stringify(date_time=datetime(2013, 06, 01, 02, 03, 04))
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
        date = datetime(2012, 2, 3, 4, 5)
        assert_equal(date, parse_pretty_date(format_pretty_date(date)))
    
    def test_parse_tag(self):
        tag = "  STRINGwithCaps and    SPaces   "
        parsed_tag = parse_tag(tag)
        assert_equal(parsed_tag, "stringwithcaps-and-spaces")


class TestUtil(TestCase):
    def test_diff_datewise(self):
        l = []
        l_just_dates = []
        r = []
        r_just_dates = []
        lp = 'blah%Y...%m...%d...%Hblahblah'
        rp = 'neenee%Y%m%d%Hneenee'
        
        expect0 = set([datetime(2012, 6, 14, 13), datetime(2012, 11, 9, 3)])
        expect1 = set([datetime(2012, 6, 14, 14), datetime(2013, 11, 10, 22)])
        
        for y in range(2012, 2014):
            for m in range(1, 13):
                # we're just diffing so we don't care about getting all days
                for d in range(1, 28):
                    for h in range(0, 24):
                        x = datetime(y, m, d, h)
                        if x not in expect1:
                            l.append(datetime.strftime(x, lp))
                            l_just_dates.append(x)
                        if x not in expect0:
                            r.append(datetime.strftime(x, rp))
                            r_just_dates.append(x)
        
        result = diff_datewise(l, r, left_parse=lp, right_parse=rp)
        self.assertEqual(result[0], expect0)
        self.assertEqual(result[1], expect1)
        
        result = diff_datewise(l_just_dates, r, right_parse=rp)
        self.assertEqual(result[0], expect0)
        self.assertEqual(result[1], expect1)
        
        result = diff_datewise(l_just_dates, r_just_dates)
        self.assertEqual(result[0], expect0)
        self.assertEqual(result[1], expect1)
    
    def test_timestamps_to_now(self):
        now = datetime.now()
        start = now - timedelta(hours=2)
        expect = [
            start,
            start + timedelta(hours=1),
            start + timedelta(hours=2),
        ]
        timestamps = timestamps_to_now(start, timedelta(hours=1))
        self.assertEqual(expect, list(timestamps))

    def test_chunk(self):
        chunked = list(chunk(range(2, 9), 2))
        assert_equal(chunked, [[2, 3], [4, 5], [6, 7], [8]])
        chunked = list(chunk(range(2, 3), 2))
        assert_equal(chunked, [[2]])

    def test_update_dict(self):
        target = {}
        source = {
            'deep dict': {'nested': {'one': 1}},
            'list': [1, 2, 3],
            'value': 1,
        }
        update_dict(target, source)
        assert_equal(target['deep dict']['nested']['one'], 1)
        assert_equal(target['list'], [1, 2, 3])
        assert_equal(target['value'], 1)

        source2 = {
            'deep dict': {'nested': {'one': 9}, 'nested1': {'two': 10}},
            'list': [4, 5],
            'value': 3,
            'value1': 2,
        }
        update_dict(target, source2)
        assert_equal(target['deep dict']['nested']['one'], 9)
        assert_equal(target['deep dict']['nested1']['two'], 10)
        assert_equal(target['list'], [1, 2, 3, 4, 5])
        assert_equal(target['value'], 3)
        assert_equal(target['value1'], 2)
