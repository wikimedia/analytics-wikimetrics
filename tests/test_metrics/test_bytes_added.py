from nose.tools import assert_true, assert_equal
from tests.fixtures import DatabaseWithCohortTest
from wikimetrics.metrics import BytesAdded


class BytesAddedTest(DatabaseWithCohortTest):
    
    def test_adds_negatives_and_positives(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-06-01 00:00:00',
            end_date='2013-08-01 00:00:00',
        )
        
        results = metric(list(self.cohort), self.mwSession)
        print results
        dan_expected = {
            'net_sum': 6,
            'absolute_sum': 14,
            'positive_only_sum': 10,
            'negative_only_sum': -4,
        }
        evan_expected = {
            'net_sum': 136,
            'absolute_sum': 144,
            'positive_only_sum': 140,
            'negative_only_sum': -4,
        }
        assert_equal(results[self.dan_id], dan_expected)
        assert_equal(results[self.evan_id], evan_expected)
    
    def test_uses_date_range(self):
        
        metric = BytesAdded(
            namespaces=[0],
        )
        assert_true(not metric.validate())
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-07-01 00:00:00',
            end_date='2013-08-01 00:00:00',
        )
        metric.fake_csrf()
        assert_true(metric.validate())
        
        results = metric(list(self.cohort), self.mwSession)
        print results
        dan_expected = {
            'net_sum': 10,
            'absolute_sum': 10,
            'positive_only_sum': 10,
            'negative_only_sum': 0,
        }
        assert_equal(
            results[self.dan_id],
            dan_expected,
        )
    
    def test_uses_summation_options(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-06-01 00:00:00',
            end_date='2013-08-01 00:00:00',
            positive_only_sum=False,
            negative_only_sum=False,
        )
        metric.fake_csrf()
        assert_true(metric.validate())
        
        results = metric(list(self.cohort), self.mwSession)
        print results
        dan_expected = {
            'net_sum': 6,
            'absolute_sum': 14,
        }
        andrew_expected = {
            'net_sum': None,
            'absolute_sum': None,
        }
        assert_equal(
            results[self.dan_id],
            dan_expected,
        )
        assert_equal(
            results[self.andrew_id],
            andrew_expected,
        )
    
    def test_counts_first_edit_on_a_page(self):
        
        metric = BytesAdded(
            namespaces=[209],
            start_date='2013-08-04 00:00:00',
            end_date='2013-08-06 00:00:00',
            positive_only_sum=False,
            negative_only_sum=False,
            absolute_sum=False,
        )
        metric.fake_csrf()
        assert_true(metric.validate())
        
        results = metric(list(self.cohort), self.mwSession)
        dan_expected = {
            'net_sum': 100,
        }
        assert_equal(
            results[self.dan_id],
            dan_expected,
        )
