from datetime import datetime, timedelta
from nose.tools import assert_true, assert_equals, assert_false

from tests.fixtures import QueueDatabaseTest
from wikimetrics.metrics import metric_classes, NewlyRegistered, NamespaceEdits
from wikimetrics.utils import r
from wikimetrics.enums import Aggregation, TimeseriesChoices
from wikimetrics.models import AggregateReport


class EdgeCasesTest(QueueDatabaseTest):
    '''
    Tests different cases for metric system when it comes to report results
    '''
    def setUp(self):
        QueueDatabaseTest.setUp(self)

    def test_aggregate_empty_results(self):
        '''
         Tests what happens when no users are
         returned for the initial metric run
         so there are no users to agreggate
         '''
        self.create_wiki_cohort()

        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2010-01-01 00:00:00',
            end_date='2010-01-02 00:00:00',
        )
        options = {
            'individualResults': True,
            'aggregateResults': True,
            'aggregateSum': True,
            'aggregateAverage': True,
            'aggregateStandardDeviation': True,
        }

        ar = AggregateReport(
            metric,
            self.basic_wiki_cohort,
            options,
            user_id=self.basic_wiki_cohort_owner,
        )
        result = ar.task.delay(ar).get()

        assert_equals(result[Aggregation.IND].keys(), [])
        assert_equals(result[Aggregation.SUM]['edits'], r(0))
        assert_equals(result[Aggregation.AVG]['edits'], r(0))
        assert_equals(result[Aggregation.STD]['edits'], r(0))
