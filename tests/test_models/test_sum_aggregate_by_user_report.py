from nose.tools import assert_equals, assert_true
from wikimetrics.metrics import metric_classes
from wikimetrics.models import SumAggregateByUserReport
from wikimetrics.models.storage.wikiuser import WikiUserKey
from wikimetrics.enums import Aggregation
from ..fixtures import DatabaseTest


class SumAggregateByUserReportWithoutQueueTest(DatabaseTest):
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()

    def test_finish_positive(self):
        metric = metric_classes['RollingActiveEditor']()
        report = SumAggregateByUserReport(self.cohort, metric)
        report.usernames = {
            WikiUserKey(1, 'enwiki', 12): 'John',
            WikiUserKey(2, 'dewiki', 12): 'John',
            WikiUserKey(3, 'frwiki', 12): 'John',
            WikiUserKey(4, 'ptwiki', 12): 'Kate',
        }
        finished = report.finish([{
            '1|enwiki|12': {'rolling_active_editor': 0},
            '2|dewiki|12': {'rolling_active_editor': 1},
            '3|frwiki|12': {'rolling_active_editor': 0},
            '4|ptwiki|12': {'rolling_active_editor': 1},
        }])
        assert_equals(len(finished), 1)
        assert_true(Aggregation.SUM in finished)
        assert_true('rolling_active_editor' in finished[Aggregation.SUM])
        assert_equals(finished[Aggregation.SUM]['rolling_active_editor'], 2)

    def test_finish_negative(self):
        metric = metric_classes['RollingActiveEditor']()
        report = SumAggregateByUserReport(self.cohort, metric)
        report.usernames = {
            WikiUserKey(1, 'enwiki', 12): 'John',
            WikiUserKey(2, 'dewiki', 12): 'John',
            WikiUserKey(3, 'frwiki', 12): 'John',
            WikiUserKey(4, 'ptwiki', 12): 'Kate',
        }
        finished = report.finish([{
            '1|enwiki|12': {'rolling_active_editor': 0},
            '2|dewiki|12': {'rolling_active_editor': 0},
            '3|frwiki|12': {'rolling_active_editor': 0},
            '4|ptwiki|12': {'rolling_active_editor': 0},
        }])
        assert_equals(len(finished), 1)
        assert_true(Aggregation.SUM in finished)
        assert_true('rolling_active_editor' in finished[Aggregation.SUM])
        assert_equals(finished[Aggregation.SUM]['rolling_active_editor'], 0)
