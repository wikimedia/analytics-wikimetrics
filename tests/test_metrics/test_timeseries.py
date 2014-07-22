from collections import OrderedDict
from datetime import datetime
from nose.tools import assert_equals
from wikimetrics.metrics.timeseries_metric import TimeseriesMetric
from wikimetrics.enums import TimeseriesChoices
from tests.fixtures import DatabaseTest


class TimeseriesTest(DatabaseTest):
    
    def test_get_date_from_tuple(self):
        m = TimeseriesMetric()
        
        date = datetime(2010, 1, 2, 3, 4, 5)
        t1 = m.get_date_from_tuple(
            (0, 0, date.year),
            2, 3
        )
        assert_equals(t1, '2010-01-01 00:00:00')
        
        t2 = m.get_date_from_tuple(
            (0, 0, date.year, date.month),
            2, 4
        )
        assert_equals(t2, '2010-01-01 00:00:00')
        
        t3 = m.get_date_from_tuple(
            (0, 0, date.year, date.month, date.day),
            2, 5
        )
        assert_equals(t3, '2010-01-02 00:00:00')
        
        t4 = m.get_date_from_tuple(
            (0, 0, date.year, date.month, date.day, date.hour),
            2, 6
        )
        assert_equals(t4, '2010-01-02 03:00:00')
    
    def normalize_datetime_slices(self):
        m = TimeseriesMetric(
            start_date='2013-01-01 23:00:00',
            end_date='2013-01-03 00:00:00',
            timeseries=TimeseriesChoices.HOUR,
        )
        
        results = {
            1: {
                'test': {
                    '2013-01-02 01:00:00': 12,
                    '2013-01-02 14:00:00': 11,
                }
            }
        }
        r = m.normalize_datetime_slices(results, [('test', 1, 0)])
        expected = OrderedDict()
        expected['2013-01-01 23:00:00'] = 0
        expected['2013-01-02 00:00:00'] = 0
        expected['2013-01-02 01:00:00'] = 12
        expected['2013-01-02 02:00:00'] = 0
        expected['2013-01-02 03:00:00'] = 0
        expected['2013-01-02 04:00:00'] = 0
        expected['2013-01-02 05:00:00'] = 0
        expected['2013-01-02 06:00:00'] = 0
        expected['2013-01-02 07:00:00'] = 0
        expected['2013-01-02 08:00:00'] = 0
        expected['2013-01-02 09:00:00'] = 0
        expected['2013-01-02 10:00:00'] = 0
        expected['2013-01-02 11:00:00'] = 0
        expected['2013-01-02 12:00:00'] = 0
        expected['2013-01-02 13:00:00'] = 0
        expected['2013-01-02 14:00:00'] = 11
        expected['2013-01-02 15:00:00'] = 0
        expected['2013-01-02 16:00:00'] = 0
        expected['2013-01-02 17:00:00'] = 0
        expected['2013-01-02 18:00:00'] = 0
        expected['2013-01-02 19:00:00'] = 0
        expected['2013-01-02 20:00:00'] = 0
        expected['2013-01-02 21:00:00'] = 0
        expected['2013-01-02 22:00:00'] = 0
        expected['2013-01-02 23:00:00'] = 0
        
        assert_equals(r, {1: {'test': expected}})
    
    def test_normalize_datetime_slices_day(self):
        m = TimeseriesMetric(
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-05 00:00:00',
            timeseries=TimeseriesChoices.DAY,
        )
        
        results = {
            1: {
                'test': {
                    '2013-01-02 00:00:00': 23,
                    '2013-01-04 00:00:00': 19,
                }
            },
            2: {
                'test': {
                    '2013-01-03 00:00:00': 23,
                    '2013-01-04 00:00:00': 19,
                }
            }
        }
        r = m.normalize_datetime_slices(results, [('test', 1, 0)])
        
        expected1 = OrderedDict()
        expected1['2013-01-01 00:00:00'] = 0
        expected1['2013-01-02 00:00:00'] = 23
        expected1['2013-01-03 00:00:00'] = 0
        expected1['2013-01-04 00:00:00'] = 19
        
        expected2 = OrderedDict()
        expected2['2013-01-01 00:00:00'] = 0
        expected2['2013-01-02 00:00:00'] = 0
        expected2['2013-01-03 00:00:00'] = 23
        expected2['2013-01-04 00:00:00'] = 19
        
        assert_equals(r[1], {'test': expected1})
        assert_equals(r[2], {'test': expected2})
    
    def test_normalize_datetime_slices_month(self):
        m = TimeseriesMetric(
            start_date='2013-01-02 00:00:00',
            end_date='2013-03-05 00:00:00',
            timeseries=TimeseriesChoices.MONTH,
        )
        
        results = {
            1: {
                'test': {
                    '2013-01-01 00:00:00': 12,
                    '2013-03-01 00:00:00': 1,
                }
            },
        }
        r = m.normalize_datetime_slices(results, [('test', 1, 0)])
        
        expected = OrderedDict()
        expected['2013-01-02 00:00:00'] = 12
        expected['2013-02-01 00:00:00'] = 0
        expected['2013-03-01 00:00:00'] = 1
        
        assert_equals(r, {1: {'test': expected}})
    
    def test_normalize_datetime_slices_year(self):
        m = TimeseriesMetric(
            start_date='2013-03-10 00:00:00',
            end_date='2015-03-05 00:00:00',
            timeseries=TimeseriesChoices.YEAR,
        )
        
        results = {
            1: {
                'test': {
                    '2013-01-01 00:00:00': 12,
                }
            },
        }
        r = m.normalize_datetime_slices(results, [('test', 1, 0)])
        
        expected = OrderedDict()
        expected['2013-03-10 00:00:00'] = 12
        expected['2014-01-01 00:00:00'] = 0
        expected['2015-01-01 00:00:00'] = 0
        
        assert_equals(r, {1: {'test': expected}})
    
    def test_normalize_datetime_slices_start_date_forces_first_interval(self):
        m = TimeseriesMetric(
            start_date='2013-01-02 00:00:00',
            end_date='2013-03-05 00:00:00',
            timeseries=TimeseriesChoices.MONTH,
        )
        
        results = {
            1: {
                'test': {
                    '2013-01-01 00:00:00': 12,
                    '2013-03-01 00:00:00': 1,
                }
            },
        }
        r = m.normalize_datetime_slices(results, [('test', 1, 0)])
        
        expected = OrderedDict()
        # The first interval starts on the 2nd and not the 1st
        expected['2013-01-02 00:00:00'] = 12
        expected['2013-02-01 00:00:00'] = 0
        expected['2013-03-01 00:00:00'] = 1
        
        assert_equals(r, {1: {'test': expected}})
    
    def test_first_date_ordered_properly_without_return_value(self):
        m = TimeseriesMetric(
            start_date='2013-01-01 00:00:00',
            end_date='2013-03-02 00:00:00',
            timeseries=TimeseriesChoices.MONTH,
        )
        
        results = {
            1: {
                'test': {
                    '2013-03-01 00:00:00': 1,
                }
            },
        }
        r = m.normalize_datetime_slices(results, [('test', 1, 0)])
        
        expected = OrderedDict()
        expected['2013-01-01 00:00:00'] = 0
        expected['2013-02-01 00:00:00'] = 0
        expected['2013-03-01 00:00:00'] = 1
        
        assert_equals(r, {1: {'test': expected}})
