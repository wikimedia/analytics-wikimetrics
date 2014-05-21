from datetime import datetime
from unittest import TestCase
from nose.tools import assert_equal, raises

from wikimetrics.models import Cohort, ValidatedCohort, WikiCohort
from wikimetrics.api import CohortService


class CohortModelsTest(TestCase):
    def setUp(self):
        self.good = GoodCohortData()
        self.bad = MissingCohortData()

    def test_plain_cohort(self):
        c = Cohort(self.good, 2)
        assert_equal(c.created, self.good.created)
        assert_equal(c.description, self.good.description)
        assert_equal(c.size, 2)

    @raises(AttributeError)
    def test_plain_cohort_bad_data(self):
        Cohort(self.bad, 2)

    def test_wiki_cohort(self):
        c = WikiCohort(self.good, 0)
        assert_equal(c.created, self.good.created)
        assert_equal(c.description, self.good.description)
        assert_equal(c.size, 0)

    @raises(AttributeError)
    def test_wiki_cohort_bad_data(self):
        WikiCohort(self.bad, 0)

    def test_validated_cohort(self):
        c = ValidatedCohort(self.good, 4)
        assert_equal(c.created, self.good.created)
        assert_equal(c.description, self.good.description)
        assert_equal(c.size, 4)

    @raises(AttributeError)
    def test_validated_cohort_bad_data(self):
        ValidatedCohort(self.bad, 4)


class GoodCohortData(object):
    id = 123
    name = 'hi'
    description = 'Hello awesome cohort\nhow are you'
    default_project = object()
    created = datetime.now()
    enabled = True
    public = True
    validated = None
    validate_as_user_ids = True
    validation_queue_key = 'blahblahblahblah'


class MissingCohortData(object):
    """
    This data is bad because it doesn't contain some of the fields required by Cohort(s)
    """
    # missing id
    # missing name
    description = 123
    default_project = object()
    created = datetime.now()
    enabled = True
    public = True
    validated = None
    # missing validate_as_user_ids
    validation_queue_key = 'blahblahblahblah'
