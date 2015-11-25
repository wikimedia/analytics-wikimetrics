from nose.tools import assert_equals, raises, assert_true, assert_is_not_none

from tests.fixtures import QueueDatabaseTest, d
from wikimetrics.models import RunProgramMetricsReport, ReportStore, WikiUserStore
from wikimetrics.utils import parse_pretty_date, format_pretty_date
from wikimetrics.enums import Aggregation
from wikimetrics.api import CohortService

cohort_service = CohortService()


def make_pending(report):
    report.status = 'PENDING'


class RunProgramMetricsReportWithInvalidCohort(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.common_cohort_1()

    @raises(Exception)
    def test_raises_unvalidated_cohort(self):
        self.cohort.validated = False
        jr = RunProgramMetricsReport(self.cohort.id,
                                     parse_pretty_date('2015-01-01 00:00:00'),
                                     parse_pretty_date('2015-01-31 00:00:00'),
                                     self.owner_user_id)
        jr.task.delay(jr).get()

    def test_invalid_cohort_returns_failure(self):
        self.cohort.validated = True
        wikiusers = self.session.query(WikiUserStore) \
            .filter(WikiUserStore.validating_cohort == self.cohort.id) \
            .all()
        # Valid cohorts have >=50% of the users valid, so we make half
        # of them invalid to test
        for wu in wikiusers[:(len(wikiusers) / 2 + 1)]:
            wu.valid = False
        self.session.commit()
        jr = RunProgramMetricsReport(self.cohort.id,
                                     parse_pretty_date('2015-01-01 00:00:00'),
                                     parse_pretty_date('2015-01-31 00:00:00'),
                                     self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        result_key = self.session.query(ReportStore) \
            .get(jr.persistent_id) \
            .result_key
        results = results[result_key]
        assert_is_not_none(results['FAILURE'])


class RunProgramMetricsReportTest(QueueDatabaseTest):
    def setUp(self):
        QueueDatabaseTest.setUp(self)
        # registration for all the editors below
        self.r = r = 20150101000000
        # exactly 30 days after registration
        self.m = m = 20150131000000
        self.r_plus_30 = format_pretty_date(d(self.m))

        self.create_test_cohort(
            editor_count=5,
            revisions_per_editor=8,
            revision_timestamps=[
                # this one will make 5 edits within 30 days of self.r_plus_30
                [r + 1, r + 2, r + 3, r + 4, r + 5, m + 6, m + 7, m + 8],
                # this one will make 3 edits within 30 days of self.r_plus_30
                [r + 1, r + 2, r + 3, m + 4, m + 5, m + 6, m + 7, m + 8],
                # this one will make 8 edits within 30 days of self.r_plus_30
                [r + 1, r + 2, r + 3, r + 4, r + 5, r + 6, r + 7, r + 8],
                # this one will make 0 edits within 30 days of self.r_plus_30
                [m + 1, m + 2, m + 3, m + 4, m + 5, m + 6, m + 7, m + 8],
                # this one will make the 5th edit right on self.r_plus_30
                [r + 1, r + 2, r + 3, r + 4, m + 0, m + 6, m + 7, m + 8],
            ],
            user_registrations=r,
            revision_lengths=10
        )

    @raises(Exception)
    def test_empty_response(self):
        """
        Case where user tries to submit form with no cohorts / metrics
        should be handled client side, on server side an exception will be
        thrown if RunProgramMetricsReport object cannot be created
        """
        jr = RunProgramMetricsReport(None, None, None, user_id=self.owner_user_id)
        jr.task.delay(jr).get()

    def test_basic_response(self):
        jr = RunProgramMetricsReport(self.cohort.id,
                                     parse_pretty_date('2015-01-01 00:00:00'),
                                     parse_pretty_date('2015-01-31 00:00:00'),
                                     self.owner_user_id)
        results = jr.task.delay(jr).get()
        self.session.commit()
        
        # Make sure the cohort is validated
        assert_true(self.cohort.validated)

        result_key = self.session.query(ReportStore) \
            .get(jr.persistent_id) \
            .result_key
        results = results[result_key]
        assert_equals(
            len(results[Aggregation.SUM]),
            6)
        assert_equals(
            results[Aggregation.SUM]['pages_created'], 1)
        assert_equals(
            results[Aggregation.SUM]['pages_edited'], 4)
        assert_equals(
            results[Aggregation.SUM]['newly_registered'], 0)
        assert_equals(
            results[Aggregation.SUM]['existing_editors'], 5)
        assert_equals(
            results[Aggregation.SUM]['rolling_active_editor'], 0)
        assert_equals(
            results[Aggregation.SUM]['bytes_added'], 10)
