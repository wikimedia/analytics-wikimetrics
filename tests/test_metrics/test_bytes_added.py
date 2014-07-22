from nose.tools import assert_true, assert_equal, assert_false
from tests.fixtures import DatabaseTest
from wikimetrics.metrics import BytesAdded
from wikimetrics.enums import TimeseriesChoices


class BytesAddedTest(DatabaseTest):
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_2()
    
    def test_filters_out_other_editors(self):
        self.common_cohort_2(cohort=False)
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-03 00:00:00',
        )
        results = metric(self.editor_ids, self.mwSession)

        assert_equal(len(results), 3)

    def test_runs_for_an_entire_wiki(self):
        self.common_cohort_2(cohort=False)
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-03 00:00:00',
        )
        results = metric(None, self.mwSession)

        assert_equal(len(results), 4)
        expected1 = {
            'net_sum': -90,
            'absolute_sum': 110,
            'positive_only_sum': 10,
            'negative_only_sum': -100,
        }
        expected2 = {
            'net_sum': 126,
            'absolute_sum': 134,
            'positive_only_sum': 130,
            'negative_only_sum': -4,
        }
        assert_equal(results[self.editors[0].user_id], expected1)
        assert_equal(results[self.editors[1].user_id], expected2)
        # NOTE: this is a bit precarious as it assumes the order of test data inserts
        assert_equal(results[self.editors[0].user_id + 3], expected1)

    def test_adds_negatives_and_positives(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-03 00:00:00',
        )
        
        results = metric(self.editor_ids, self.mwSession)
        expected1 = {
            'net_sum': -90,
            'absolute_sum': 110,
            'positive_only_sum': 10,
            'negative_only_sum': -100,
        }
        expected2 = {
            'net_sum': 126,
            'absolute_sum': 134,
            'positive_only_sum': 130,
            'negative_only_sum': -4,
        }
        assert_equal(results[self.editors[0].user_id], expected1)
        assert_equal(results[self.editors[1].user_id], expected2)
    
    def test_uses_date_range(self):
        
        metric = BytesAdded(
            start_date='blah'
        )
        assert_false(metric.validate())
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:40:00',
            end_date='2013-02-01 01:01:00',
        )
        assert_true(metric.validate())
        
        results = metric(self.editor_ids, self.mwSession)
        expected1 = {
            'net_sum': 10,
            'absolute_sum': 10,
            'positive_only_sum': 10,
            'negative_only_sum': 0,
        }
        assert_equal(results[self.editors[0].user_id], expected1)
    
    def test_uses_summation_options(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-03 00:00:00',
            positive_only_sum=False,
            negative_only_sum=False,
        )
        assert_true(metric.validate())
        
        results = metric(self.editor_ids, self.mwSession)
        expected1 = {
            'net_sum': -90,
            'absolute_sum': 110,
        }
        expected3 = {
            'net_sum': 0,
            'absolute_sum': 0,
        }
        assert_equal(results[self.editors[0].user_id], expected1)
        assert_equal(results[self.editors[2].user_id], expected3)
    
    def test_counts_first_edit_on_a_page(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2012-12-31 00:00:00',
            end_date='2013-01-01 00:00:00',
            positive_only_sum=False,
            negative_only_sum=False,
            absolute_sum=False,
        )
        assert_true(metric.validate())
        
        results = metric(self.editor_ids, self.mwSession)
        expected1 = {
            'net_sum': 100,
        }
        assert_equal(results[self.editors[0].user_id], expected1)


class BytesAddedTimeseriesTest(DatabaseTest):
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_3()
    
    def test_timeseries_by_hour(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-01 03:00:00',
            positive_only_sum=False,
            negative_only_sum=False,
            absolute_sum=False,
            timeseries=TimeseriesChoices.HOUR,
        )
        
        results = metric(self.editor_ids, self.mwSession)
        expected1 = {
            'net_sum': {
                '2013-01-01 00:00:00' : 0,
                '2013-01-01 01:00:00' : 100,
                '2013-01-01 02:00:00' : 0,
            }
        }
        assert_equal(results[self.editors[0].user_id], expected1)
    
    def test_timeseries_by_day(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2012-12-31 09:00:00',
            end_date='2013-01-14 00:00:00',
            positive_only_sum=False,
            negative_only_sum=False,
            absolute_sum=False,
            timeseries=TimeseriesChoices.DAY,
        )
        
        results = metric(self.editor_ids, self.mwSession)
        expected1 = {
            'net_sum': {
                '2012-12-31 09:00:00' : 0,
                '2013-01-01 00:00:00' : 100,
                '2013-01-02 00:00:00' : 0,
                '2013-01-03 00:00:00' : 0,
                '2013-01-04 00:00:00' : 0,
                '2013-01-05 00:00:00' : 0,
                '2013-01-06 00:00:00' : 0,
                '2013-01-07 00:00:00' : 0,
                '2013-01-08 00:00:00' : 0,
                '2013-01-09 00:00:00' : 0,
                '2013-01-10 00:00:00' : 0,
                '2013-01-11 00:00:00' : 0,
                '2013-01-12 00:00:00' : 0,
                '2013-01-13 00:00:00' : 0,
            }
        }
        assert_equal(results[self.editors[0].user_id], expected1)
    
    def test_timeseries_by_month(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2013-04-06 00:00:00',
            positive_only_sum=False,
            negative_only_sum=False,
            absolute_sum=False,
            timeseries=TimeseriesChoices.MONTH,
        )
        
        results = metric(self.editor_ids, self.mwSession)
        expected1 = {
            'net_sum': {
                '2013-01-01 00:00:00' : 100,
                '2013-02-01 00:00:00' : -1300,
                '2013-03-01 00:00:00' : 200,
                '2013-04-01 00:00:00' : 90,
            }
        }
        assert_equal(results[self.editors[0].user_id], expected1)
    
    def test_timeseries_by_year(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2014-01-14 00:00:00',
            positive_only_sum=False,
            negative_only_sum=False,
            absolute_sum=False,
            timeseries=TimeseriesChoices.YEAR,
        )
        
        results = metric(self.editor_ids, self.mwSession)
        expected1 = {
            'net_sum': {
                '2013-01-01 00:00:00' : -910,
                '2014-01-01 00:00:00' : 0,
            }
        }
        assert_equal(results[self.editors[0].user_id], expected1)
