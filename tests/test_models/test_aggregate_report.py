from nose.tools import assert_equals, assert_true

from wikimetrics.utils import r
from wikimetrics.enums import Aggregation, TimeseriesChoices
from wikimetrics.metrics import metric_classes, NamespaceEdits
from wikimetrics.models import AggregateReport, CohortStore
from ..fixtures import QueueDatabaseTest, DatabaseTest


class AggregateReportTest(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_basic_response(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-01-01 00:00:00',
            end_date='2013-01-02 00:00:00',
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
            self.cohort,
            options,
            user_id=self.owner_user_id,
        )
        result = ar.task.delay(ar).get()
        
        assert_equals(
            result[Aggregation.IND][self.editor(0)]
            ['edits'],
            2
        )
        assert_equals(
            result[Aggregation.AVG]['edits'],
            r(1.0)
        )
        assert_equals(
            result[Aggregation.STD]['edits'],
            r(1.0)
        )


class AggregateReportWithoutQueueTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_finish(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-05-01 00:00:00',
            end_date='2013-09-01 00:00:00',
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
            self.cohort,
            options,
            user_id=self.owner_user_id,
        )
        
        finished = ar.finish([
            {
                1: {'edits': 2},
                2: {'edits': 3},
                3: {'edits': 0},
                None: {'edits': 0}
            },
        ])
        
        assert_equals(
            finished[Aggregation.SUM]['edits'],
            5
        )
        assert_equals(
            finished[Aggregation.AVG]['edits'],
            r(1.25)
        )
        
        finished = ar.finish([
            {
                1: {'other_sub_metric': r(2.3)},
                2: {'other_sub_metric': r(3.4)},
                3: {'other_sub_metric': r(0.0)},
                None: {'other_sub_metric': 0}
            },
        ])
        
        assert_equals(
            finished[Aggregation.SUM]['other_sub_metric'],
            r(5.7)
        )
        assert_equals(
            finished[Aggregation.AVG]['other_sub_metric'],
            r(1.425)
        )
        assert_equals(
            finished[Aggregation.STD]['other_sub_metric'],
            r(1.4771)
        )
    
    def test_does_not_aggregate_null_values(self):
        metric = metric_classes['Threshold'](
            name='Threshold',
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
            self.cohort,
            options,
            user_id=self.owner_user_id,
        )
        
        finished = ar.finish([
            {
                1: {'edits': 2, 'submetric': 1},
                2: {'edits': 3, 'submetric': None},
                3: {'edits': 0, 'submetric': 3},
                None: {'edits': 0}
            },
        ])
        
        assert_equals(
            finished[Aggregation.SUM]['submetric'],
            4
        )
        assert_equals(
            finished[Aggregation.AVG]['submetric'],
            2
        )
    
    def test_repr(self):
        metric = metric_classes['NamespaceEdits'](
            name='NamespaceEdits',
            namespaces=[0, 1, 2],
            start_date='2013-05-01 00:00:00',
            end_date='2013-09-01 00:00:00',
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
            self.cohort,
            options,
            user_id=self.owner_user_id,
        )
        
        assert_true(str(ar).find('AggregateReport') >= 0)


class AggregateReportTimeseriesTest(QueueDatabaseTest):
    
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_timeseries_day(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2012-12-31 00:00:00',
            end_date='2013-01-03 00:00:00',
            timeseries=TimeseriesChoices.DAY,
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
            self.cohort,
            options,
            user_id=self.owner_user_id,
        )
        results = ar.task.delay(ar).get()
        
        self.session.commit()
        
        assert_equals(
            results[Aggregation.IND][self.editor(0)]['edits'],
            {
                '2012-12-31 00:00:00' : 1,
                '2013-01-01 00:00:00' : 2,
                '2013-01-02 00:00:00' : 0,
            }
        )
        assert_equals(
            results[Aggregation.SUM]['edits'],
            {
                '2012-12-31 00:00:00' : 1,
                '2013-01-01 00:00:00' : 5,
                '2013-01-02 00:00:00' : 2,
            }
        )
        assert_equals(
            results[Aggregation.AVG]['edits'],
            {
                '2012-12-31 00:00:00' : r(0.25),
                '2013-01-01 00:00:00' : r(1.25),
                '2013-01-02 00:00:00' : r(0.5),
            }
        )
        assert_equals(
            results[Aggregation.STD]['edits'],
            {
                '2012-12-31 00:00:00' : r(0.4330),
                '2013-01-01 00:00:00' : r(0.4330),
                '2013-01-02 00:00:00' : r(0.8660),
            }
        )
    
    def test_finish_timeseries(self):
        metric = NamespaceEdits(
            namespaces=[0],
            start_date='2012-12-31 00:00:00',
            end_date='2013-01-03 00:00:00',
            timeseries=TimeseriesChoices.DAY,
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
            self.cohort,
            options,
            user_id=self.owner_user_id,
        )
        
        finished = ar.finish([
            {
                1: {'edits': {'date1': 1, 'date2': 2}},
                2: {'edits': {'date1': 0, 'date2': 1}},
                3: {'edits': {'date1': 0, 'date2': 0}},
                None: {'edits': {'date1': None, 'date2': None}}
            },
        ])
        
        assert_equals(
            finished[Aggregation.SUM]['edits'],
            {'date1': 1, 'date2': 3}
        )
        assert_equals(
            finished[Aggregation.AVG]['edits'],
            {'date1': r(0.3333), 'date2': r(1.0)}
        )
        assert_equals(
            finished[Aggregation.STD]['edits'],
            {'date1': r(0.4714), 'date2': r(0.8165)}
        )
        
        finished = ar.finish([
            {
                1: {'other_sub_metric': {'date3': r(2.3), 'date4': 0}},
                2: {'other_sub_metric': {'date3': 0, 'date4': r(3.4)}},
                3: {'other_sub_metric': {'date3': None, 'date4': None}},
                None: {'other_sub_metric': {'date3': None, 'date4': None}}
            },
        ])
        
        assert_equals(
            finished[Aggregation.SUM]['other_sub_metric'],
            {'date3': r(2.3), 'date4': r(3.4)}
        )
        assert_equals(
            finished[Aggregation.AVG]['other_sub_metric'],
            {'date3': r(1.15), 'date4': r(1.7)}
        )
        assert_equals(
            finished[Aggregation.STD]['other_sub_metric'],
            {'date3': r(1.15), 'date4': r(1.7)}
        )

"""
NOTE: a sample output of AggregateReport:
{
    'Standard Deviation': {
        'edits': 'Not Implemented'
    },
    'Individual Results': [
        {
            1: {'edits': 2},
            2: {'edits': 3},
            3: {'edits': 0},
            #None: {'edits': 0}
        }
    ],
    'Sum': {
        'edits': Decimal('5')
    },
    'Average': {
        'edits': Decimal('1.25')
    }
}
"""
