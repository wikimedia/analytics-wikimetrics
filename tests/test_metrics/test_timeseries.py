from datetime import datetime
from nose.tools import assert_equals
from wikimetrics.metrics.timeseries_metric import (
    TimeseriesMetric,
    TimeseriesChoices,
)
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
    
    def test_fill_in_missing_datetimes_hour(self):
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
        r = m.fill_in_missing_datetimes(results, [('test', 1, 0)])
        assert_equals(r, {
            1: {
                'test': {
                    '2013-01-01 23:00:00': 0,
                    '2013-01-02 00:00:00': 0,
                    '2013-01-02 01:00:00': 12,
                    '2013-01-02 02:00:00': 0,
                    '2013-01-02 03:00:00': 0,
                    '2013-01-02 04:00:00': 0,
                    '2013-01-02 05:00:00': 0,
                    '2013-01-02 06:00:00': 0,
                    '2013-01-02 07:00:00': 0,
                    '2013-01-02 08:00:00': 0,
                    '2013-01-02 09:00:00': 0,
                    '2013-01-02 10:00:00': 0,
                    '2013-01-02 11:00:00': 0,
                    '2013-01-02 12:00:00': 0,
                    '2013-01-02 13:00:00': 0,
                    '2013-01-02 14:00:00': 11,
                    '2013-01-02 15:00:00': 0,
                    '2013-01-02 16:00:00': 0,
                    '2013-01-02 17:00:00': 0,
                    '2013-01-02 18:00:00': 0,
                    '2013-01-02 19:00:00': 0,
                    '2013-01-02 20:00:00': 0,
                    '2013-01-02 21:00:00': 0,
                    '2013-01-02 22:00:00': 0,
                    '2013-01-02 23:00:00': 0,
                }
            }
        })
    
    def test_fill_in_missing_datetimes_day(self):
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
        r = m.fill_in_missing_datetimes(results, [('test', 1, 0)])
        
        assert_equals(r, {
            1: {
                'test': {
                    '2013-01-01 00:00:00': 0,
                    '2013-01-02 00:00:00': 23,
                    '2013-01-03 00:00:00': 0,
                    '2013-01-04 00:00:00': 19,
                }
            },
            2: {
                'test': {
                    '2013-01-01 00:00:00': 0,
                    '2013-01-02 00:00:00': 0,
                    '2013-01-03 00:00:00': 23,
                    '2013-01-04 00:00:00': 19,
                }
            }
        })
    
    def test_fill_in_missing_datetimes_month(self):
        m = TimeseriesMetric(
            start_date='2013-01-02 00:00:00',
            end_date='2013-03-05 00:00:00',
            timeseries=TimeseriesChoices.MONTH,
        )
        
        results = {
            1: {
                'test': {
                    '2013-01-02 00:00:00': 12,
                    '2013-03-02 00:00:00': 1,
                }
            },
        }
        r = m.fill_in_missing_datetimes(results, [('test', 1, 0)])
        
        assert_equals(r, {
            1: {
                'test': {
                    '2013-01-02 00:00:00': 12,
                    '2013-02-02 00:00:00': 0,
                    '2013-03-02 00:00:00': 1,
                }
            },
        })
    
    def test_fill_in_missing_datetimes_year(self):
        m = TimeseriesMetric(
            start_date='2013-03-10 00:00:00',
            end_date='2015-03-05 00:00:00',
            timeseries=TimeseriesChoices.YEAR,
        )
        
        results = {
            1: {
                'test': {
                    '2013-03-10 00:00:00': 12,
                }
            },
        }
        r = m.fill_in_missing_datetimes(results, [('test', 1, 0)])
        
        assert_equals(r, {
            1: {
                'test': {
                    '2013-03-10 00:00:00': 12,
                    '2014-03-10 00:00:00': 0,
                }
            },
        })
