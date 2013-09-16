from datetime import datetime
from nose.tools import assert_equals
from wikimetrics.metrics.timeseries_metric import (
    TimeseriesMetric,
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
        assert_equals(t1, '2010')
        
        t2 = m.get_date_from_tuple(
            (0, 0, date.year, date.month),
            2, 4
        )
        assert_equals(t2, '2010-01')
        
        t3 = m.get_date_from_tuple(
            (0, 0, date.year, date.month, date.day),
            2, 5
        )
        assert_equals(t3, '2010-01-02')
        
        t4 = m.get_date_from_tuple(
            (0, 0, date.year, date.month, date.day, date.hour),
            2, 6
        )
        assert_equals(t4, '2010-01-02 03:00:00')
