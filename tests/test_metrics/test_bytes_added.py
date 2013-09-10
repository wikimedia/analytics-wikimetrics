from nose.tools import assert_true, assert_equal
from tests.fixtures import DatabaseTest
from wikimetrics.metrics import BytesAdded


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
