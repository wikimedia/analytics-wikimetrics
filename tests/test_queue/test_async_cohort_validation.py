from nose.tools import assert_not_equals, assert_equals
from tests.fixtures import QueueTest, QueueDatabaseTest
from wikimetrics.models import MetricReport
from wikimetrics.configurables import db
from wikimetrics.metrics import RandomMetric
from wikimetrics.models.cohort_upload_node import ValidateCohort
from wikimetrics.models import (
    MediawikiUser, Cohort, WikiUser
)
from pprint import pprint
import sys


class ValidateCohortTest(QueueDatabaseTest):

    def setUp(self):
        QueueDatabaseTest.setUp(self)

        db_session = self.mwSession
        db_session.add(MediawikiUser(user_name="Editor test-specific-0"))
        db_session.add(MediawikiUser(user_name="Editor test-specific-1"))
        db_session.commit()
        #self.common_cohort_1()
        #session = db.get_session()
        #session.
        pass

    def test_small_cohort(self):
        records = [
            # two existing users
            {"raw_username": "Editor test-specific-0",
             "project": "enwiki"},
            {"raw_username": "Editor test-specific-1",
             "project": "enwiki"},

            # one invalid username
            # NOTE: we're assuming the project will be valid since
            # otherwise db.get_mw_session(project) will break inside get_wikiuser_by_name,
            # get_wikiuser_by_id
            # since the project is invalid. So we won't test for that
            {"raw_username": "Nonexisting",
             "project": "enwiki"},
        ]

        session = self.session
        for r in records:
            r["username"] = r["raw_username"]
        v = ValidateCohort(records, "small_cohort", "cohort_desc", "enwiki")
        async_result = v.task.delay(v)
        sync_result = async_result.get()

        pprint(sync_result)

        assert_equals(session.query(WikiUser).filter(
            WikiUser.mediawiki_username == 'Editor test-specific-0').one().valid, True)
        assert_equals(session.query(WikiUser).filter(
            WikiUser.mediawiki_username == 'Editor test-specific-1').one().valid, True)
        assert_equals(session.query(WikiUser).filter(
            WikiUser.mediawiki_username == 'Nonexisting').one().valid, False)
