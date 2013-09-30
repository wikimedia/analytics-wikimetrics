from nose.tools import assert_true, assert_equal
from tests.fixtures import DatabaseTest
from wikimetrics.metrics import BytesAdded, TimeseriesChoices


class BytesAddedTest(DatabaseTest):
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.create_test_cohort(
            editor_count=3,
            revisions_per_editor=3,
            revision_timestamps=[
                [20121231230000, 20130101003000, 20130101010000],
                [20130101120000, 20130102000000, 20130102120000],
                [None, None, None],
            ],
            revision_lengths=[
                [100, 0, 10],
                [100, 140, 136],
                [None, None, None],
            ],
        )
    
    def test_adds_negatives_and_positives(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-03 00:00:00',
        )
        
        results = metric(list(self.cohort), self.mwSession)
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
            namespaces=[0],
        )
        assert_true(not metric.validate())
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-01-01 00:40:00',
            end_date='2013-02-01 01:01:00',
        )
        metric.fake_csrf()
        assert_true(metric.validate())
        
        results = metric(list(self.cohort), self.mwSession)
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
        metric.fake_csrf()
        assert_true(metric.validate())
        
        results = metric(list(self.cohort), self.mwSession)
        expected1 = {
            'net_sum': -90,
            'absolute_sum': 110,
        }
        expected3 = {
            'net_sum': None,
            'absolute_sum': None,
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
        metric.fake_csrf()
        assert_true(metric.validate())
        
        results = metric(list(self.cohort), self.mwSession)
        expected1 = {
            'net_sum': 100,
        }
        assert_equal(results[self.editors[0].user_id], expected1)


class BytesAddedTimeseriesTest(DatabaseTest):
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.create_test_cohort(
            editor_count=4,
            revisions_per_editor=4,
            # in order, all in 2013:
            # 1/1, 1/5, 1/9, 1/13, 2/2, 2/6, 2/10, 2/14, 3/3, 3/7, 3/15, 4/4, 4/12, 4/16
            revision_timestamps=[
                [20130101010000, 20130202000000, 20130303000000, 20130404000000],
                [20130105000000, 20130206000000, 20130307000000, 20130408000000],
                [20130109000000, 20130210000000, 20130311000000, 20130412000000],
                [20130113000000, 20130214000000, 20130315000000, 20130416000000],
            ],
            # in order:
            # 100,1100,1200,1300,0,200,400,600,800,700,600,500,590,550,600,650
            revision_lengths=[
                [100, 0, 800, 590],
                [1100, 200, 700, 550],
                [1200, 400, 600, 600],
                [1300, 600, 500, 650],
            ],
        )
    
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
        
        results = metric(list(self.cohort), self.mwSession)
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
        
        results = metric(list(self.cohort), self.mwSession)
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
        
        results = metric(list(self.cohort), self.mwSession)
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
        
        results = metric(list(self.cohort), self.mwSession)
        expected1 = {
            'net_sum': {
                '2013-01-01 00:00:00' : -910,
                '2014-01-01 00:00:00' : 0,
            }
        }
        assert_equal(results[self.editors[0].user_id], expected1)
