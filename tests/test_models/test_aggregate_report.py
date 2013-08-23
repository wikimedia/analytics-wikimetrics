from decimal import Decimal
from nose.tools import assert_equals, assert_true
from wikimetrics.metrics import metric_classes
from wikimetrics.models import (
    Aggregation, AggregateReport, PersistentReport, Cohort,
)
from ..fixtures import QueueDatabaseTest, DatabaseTest


class AggregateReportTest(QueueDatabaseTest):
    
    def test_basic_response(self):
        cohort = self.session.query(Cohort).get(self.test_cohort_id)
        metric = metric_classes['NamespaceEdits'](
            name = 'NamespaceEdits',
            namespaces = [0, 1, 2],
            start_date = '2013-06-01',
            end_date = '2013-09-01',
        )
        ar = AggregateReport(
            cohort,
            metric,
            individual=True,
            aggregate=True,
            aggregate_sum=True,
            aggregate_average=True,
            aggregate_std_deviation=True,
            user_id=self.test_user_id,
        )
        result = ar.task.delay(ar).get()
        
        aggregate_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == ar.persistent_id)\
            .one()\
            .result_key
        inner_key = self.session.query(PersistentReport)\
            .filter(PersistentReport.id == ar.children[0].persistent_id)\
            .one()\
            .result_key
        
        assert_equals(
            result
                [aggregate_key]
                [Aggregation.IND]
                [0]
                [self.test_mediawiki_user_id]
                ['edits'],
            2
        )
        assert_equals(
            result
                [aggregate_key]
                [Aggregation.AVG]
                ['edits'],
            Decimal(1.25)
        )


class AggregateReportWithoutQueueTest(DatabaseTest):
    
    def test_finish(self):
        cohort = self.session.query(Cohort).get(self.test_cohort_id)
        metric = metric_classes['NamespaceEdits'](
            name = 'NamespaceEdits',
            namespaces = [0, 1, 2],
            start_date = '2013-06-01',
            end_date = '2013-09-01',
        )
        ar = AggregateReport(
            cohort,
            metric,
            individual=True,
            aggregate=True,
            aggregate_sum=True,
            aggregate_average=True,
            aggregate_std_deviation=True,
            user_id=self.test_user_id,
        )
        
        finished = ar.finish([
            {
                'namespace edits - fake cohort' : {
                    1: {'edits': 2},
                    2: {'edits': 3},
                    3: {'edits': 0},
                    None: {'edits': 0}
                }
            },
            {
                'some other metric - fake cohort' : {
                    1: {'other_sub_metric': Decimal(2.3)},
                    2: {'other_sub_metric': Decimal(3.4)},
                    3: {'other_sub_metric': Decimal(0.0)},
                    None: {'other_sub_metric': 0}
                }
            },
        ])
        
        assert_equals(
            finished[ar.result_key][Aggregation.SUM]['edits'],
            5
        )
        assert_equals(
            finished[ar.result_key][Aggregation.SUM]['other_sub_metric'],
            Decimal(5.7)
        )
        assert_equals(
            finished[ar.result_key][Aggregation.AVG]['edits'],
            # TODO: Again, figure out this crazy "None" user id
            Decimal(1.25)
        )
        assert_equals(
            finished[ar.result_key][Aggregation.AVG]['other_sub_metric'],
            Decimal(1.425)
        )
    
    def test_repr(self):
        cohort = self.session.query(Cohort).get(self.test_cohort_id)
        metric = metric_classes['NamespaceEdits'](
            name = 'NamespaceEdits',
            namespaces = [0, 1, 2],
            start_date = '2013-06-01',
            end_date = '2013-09-01',
        )
        ar = AggregateReport(
            cohort,
            metric,
            individual=True,
            aggregate=True,
            aggregate_sum=True,
            aggregate_average=True,
            aggregate_std_deviation=True,
            user_id=self.test_user_id,
        )
        
        assert_true(str(ar).find('AggregateReport') >= 0)

# NOTE: a sample output of AggregateReport:
#{
    #'f5ca5afe-6b2d-4052-bd51-6cbeaeba5eb9': {
        #'Standard Deviation': {
            #'edits': 'Not Implemented'
        #},
        #'Individual Results': [
            #{
                #1: {'edits': 2},
                #2: {'edits': 3},
                #3: {'edits': 0},
                #None: {'edits': 0}
            #}
        #],
        #'Sum': {
            #'edits': Decimal('5')
        #},
        #'Average': {
            #'edits': Decimal('1.25')
        #}
    #},
    #'f5930c16-03ba-4069-a05e-e57f9f8e2f5c': {
        #1: {'edits': 2},
        #2: {'edits': 3},
        #3: {'edits': 0},
        #None: {'edits': 0}
    #}
#}
