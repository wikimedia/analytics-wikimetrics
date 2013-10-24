from datetime import datetime, timedelta
from nose.tools import assert_true

from tests.fixtures import DatabaseTest, i, d
from wikimetrics.metrics import NamespaceEdits


class ManualLoad(DatabaseTest):
    
    def setUp(self):
        editor_count    = 10000
        revision_count  = 10
        
        one_hour = timedelta(hours=1)
        start = datetime.now() - one_hour * editor_count * 2
        
        timestamps = [
            [i(start + one_hour * (rev + edi)) for rev in range(revision_count)]
            for edi in range(editor_count)
        ]
        
        DatabaseTest.setUp(self)
        self.create_test_cohort(
            editor_count=editor_count,
            revisions_per_editor=revision_count,
            user_registrations=[i(d(t[0]) - one_hour) for t in timestamps],
            revision_timestamps=timestamps,
            revision_lengths=10,
        )
    
    def test_edits_runs(self):
        m = NamespaceEdits(
            start_date=self.revisions[0].rev_timestamp,
            end_date=self.revisions[-1].rev_timestamp,
        )
        results = m(list(self.cohort), self.mwSession)
        print('{0} results for {1} editors'.format(len(results), len(self.editors)))
        assert_true(len(results) == len(self.editors))
