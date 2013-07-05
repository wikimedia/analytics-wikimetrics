from nose.tools import assert_true, assert_not_equal, assert_equal
from tests.fixtures import DatabaseWithCohortTest

from wikimetrics import app
from wikimetrics.metrics import BytesAdded
from wikimetrics.models import Cohort, MetricJob, WikiUser, CohortWikiUser


class BytesAddedTest(DatabaseWithCohortTest):
    
    def test_adds_negatives_and_positives(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-06-01',
            end_date='2013-08-01',
        )
        
        results = metric(list(self.cohort), self.mwSession)
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
            start_date='2013-07-01',
            end_date='2013-08-01',
        )
        assert_true(metric.validate())
        
        results = metric(list(self.cohort), self.mwSession)
        dan_expected = {
            'net_sum': 10,
            'absolute_sum': 10,
            'positive_only_sum': 10,
            'negative_only_sum': 0,
        }
        assert_equal(
            results[self.dan_id],
            dan_expected,
            'did not get the results expected'
        )
    
    def test_uses_summation_options(self):
        
        metric = BytesAdded(
            namespaces=[0],
            start_date='2013-06-01',
            end_date='2013-08-01',
            positive_total=False,
            negative_total=False,
        )
        assert_true(metric.validate())
        
        results = metric(list(self.cohort), self.mwSession)
        dan_expected = {
            'net_sum': 6,
            'absolute_sum': 14,
        }
        assert_equal(
            results[self.dan_id],
            dan_expected,
            'did not get the results expected'
        )
