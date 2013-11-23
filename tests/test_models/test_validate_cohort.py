import unittest
from nose.tools import assert_equal, raises, assert_true, assert_false
from tests.fixtures import WebTest, QueueDatabaseTest
from wikimetrics.controllers.forms import CohortUpload
from wikimetrics.models import (
    MediawikiUser, Cohort, WikiUser, ValidateCohort, User,
    normalize_project,
)


class ValidateCohortTest(WebTest):
    
    def test_normalize_project_shorthand(self):
        normal = normalize_project('en')
        assert_equal(normal, 'enwiki')
    
    def test_normalize_project_uppercase(self):
        normal = normalize_project('ENWIKI')
        assert_equal(normal, 'enwiki')
    
    def test_normalize_project_nonexistent(self):
        normal = normalize_project('blah')
        assert_equal(normal, None)
    
    def test_validate_cohorts(self):
        self.helper_reset_validation()
        self.cohort.validate_as_user_ids = False
        self.session.commit()
        v = ValidateCohort(self.cohort)
        v.validate_records(self.session, self.cohort)
        
        assert_equal(self.cohort.validated, True)
        assert_equal(len(
            self.session.query(WikiUser)
                .filter(WikiUser.validating_cohort == self.cohort.id)
                .filter(WikiUser.valid)
                .all()
        ), 4)
    
    def test_validate_cohorts_with_invalid_wikiusers(self):
        self.helper_reset_validation()
        self.cohort.validate_as_user_ids = False
        wikiusers = self.session.query(WikiUser).all()
        wikiusers[0].project = 'blah'
        wikiusers[1].mediawiki_username = 'blah'
        self.session.commit()
        v = ValidateCohort(self.cohort)
        v.validate_records(self.session, self.cohort)
        
        assert_equal(self.cohort.validated, True)
        assert_equal(len(
            self.session.query(WikiUser)
                .filter(WikiUser.validating_cohort == self.cohort.id)
                .filter(WikiUser.valid)
                .all()
        ), 2)
        assert_equal(len(
            self.session.query(WikiUser)
                .filter(WikiUser.validating_cohort == self.cohort.id)
                .filter(WikiUser.valid.in_([False]))
                .all()
        ), 2)


class ValidateCohortQueueTest(QueueDatabaseTest):

    def setUp(self):
        QueueDatabaseTest.setUp(self)
        
        self.mwSession.add(MediawikiUser(user_name='Editor test-specific-0'))
        self.mwSession.add(MediawikiUser(user_name='Editor test-specific-1'))
        self.mwSession.commit()
        
        owner_user = User()
        self.session.add(owner_user)
        self.session.commit()
        self.owner_user_id = owner_user.id
    
    def test_small_cohort(self):
        cohort_upload = CohortUpload()
        cohort_upload.name.data = 'small_cohort'
        cohort_upload.project.data = 'enwiki'
        cohort_upload.records = [
            # two existing users
            {'username': 'Editor test-specific-0', 'project': 'enwiki'},
            {'username': 'Editor test-specific-1', 'project': 'enwiki'},
            # one invalid username
            {'username': 'Nonexisting', 'project': 'enwiki'},
            # one user with invalid project
            {'username': 'Nonexisting2', 'project': 'Nonexisting'},
        ]
        
        v = ValidateCohort.from_upload(cohort_upload, self.owner_user_id)
        v.task.delay(v).get()
        self.session.commit()
        
        assert_equal(self.session.query(WikiUser).filter(
            WikiUser.mediawiki_username == 'Editor test-specific-0').one().valid, True)
        assert_equal(self.session.query(WikiUser).filter(
            WikiUser.mediawiki_username == 'Editor test-specific-1').one().valid, True)
        assert_equal(self.session.query(WikiUser).filter(
            WikiUser.mediawiki_username == 'Nonexisting').one().valid, False)
        assert_equal(self.session.query(WikiUser).filter(
            WikiUser.mediawiki_username == 'Nonexisting2').one().valid, False)
    
    def test_from_upload_exception(self):
        cohort_upload = CohortUpload()
        cohort_upload.name.data = 'small_cohort'
        cohort_upload.project.data = 'enwiki'
        cohort_upload.records = [{'fake': 'dict'}]
        
        v = ValidateCohort.from_upload(cohort_upload, self.owner_user_id)
        assert_equal(v, None)


class BasicTests(unittest.TestCase):
    
    def test_repr(self):
        cohort = Cohort(id=1)
        v = ValidateCohort(cohort)
        assert_equal(str(v), '<ValidateCohort("1")>')
