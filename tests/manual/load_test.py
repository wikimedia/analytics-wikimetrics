from datetime import datetime, timedelta
from nose.tools import assert_true, assert_equal

from tests.fixtures import DatabaseTest, i, d
from wikimetrics.metrics import NamespaceEdits


class ManualLoad(DatabaseTest):
    
    def setUp(self):
        self.editor_count    = 100000
        self.revision_count  = 2
        
        one_hour = timedelta(hours=1)
        start = datetime.now() - one_hour * self.editor_count * 2
        
        timestamps = [
            [i(start + one_hour * (rev + edi)) for rev in range(self.revision_count)]
            for edi in range(self.editor_count)
        ]
        
        DatabaseTest.setUp(self)
        self.create_test_cohort(
            editor_count=self.editor_count,
            revisions_per_editor=self.revision_count,
            user_registrations=[i(d(t[0]) - one_hour) for t in timestamps],
            revision_timestamps=timestamps,
            revision_lengths=10,
        )
    
    def test_edits_runs(self):
        one_day = timedelta(days=1)
        metric = NamespaceEdits(
            start_date=self.revisions[0].rev_timestamp - one_day,
            end_date=self.revisions[-1].rev_timestamp + one_day,
        )
        results = metric(self.editor_ids, self.mwSession)
        print('{0} results for {1} editors'.format(len(results), len(self.editors)))
        assert_true(len(results) == len(self.editors))
        assert_equal(results[self.editors[0].user_id]['edits'], self.revision_count)
