from nose.tools import assert_true, assert_equals, assert_equal
import celery
from wikimetrics.models import (
    PersistentJob,
    User,
    UserRole,
    Cohort,
    CohortUser,
    CohortUserRole,
    CohortWikiUser,
    WikiUser,
    Logging,
    Page,
    MediawikiUser,
    Revision,
)
from tests.fixtures import DatabaseTest


class TestMappings(DatabaseTest):
    #***********
    # Mapping tests for our custom tables
    #***********

    def test_job(self):
        j = self.session.query(PersistentJob).get(1)
        assert_true(j.status == celery.states.PENDING)
    
    def test_user(self):
        u = self.session.query(User).get(1)
        assert_true(u.username == 'Dan')
        assert_true(u.role == UserRole.GUEST)
    
    def test_wikiuser(self):
        wu = self.session.query(WikiUser).get(1)
        assert_equals(wu.mediawiki_username, 'Dan')
    
    def test_cohort(self):
        c = self.session.query(Cohort).get(1)
        assert_equals(c.name, 'test')
        assert_true(c.public is True)
        
    def test_cohort_user(self):
        cu = self.session.query(CohortUser).get(1)
        assert_equals(cu.user_id, 1)
        assert_equals(cu.cohort_id, 1)
    
    def test_cohort_wikiuser(self):
        cwu = self.session.query(CohortWikiUser).get(1)
        assert_equals(cwu.wiki_user_id, 1)
        assert_equals(cwu.cohort_id, 1)
    
    #***********
    # Mapping tests for mediawiki tables
    #***********
    def test_mediawiki_logging(self):
        row = self.mwSession.query(Logging).get(1)
        assert_equals(row.log_user_text, 'Reedy')
    
    def test_mediawiki_user(self):
        row = self.mwSession.query(MediawikiUser).get(2)
        assert_equals(row.user_name, 'Evan')
    
    def test_mediawiki_page(self):
        row = self.mwSession.query(Page).get(1)
        assert_equals(row.page_title, 'Main_Page')
    
    def test_mediawiki_revision(self):
        row = self.mwSession.query(Revision).get(2)
        assert_equals(row.rev_comment, 'Dan edit 1')
    
    #***********
    # Join tests
    #***********
    def test_cohort_members(self):
        user_ids = self.session\
            .query(WikiUser.mediawiki_userid)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == 1)\
            .all()
        
        assert_true(len(user_ids) == 4, "Cohort 1 should have 4 wiki users in it")
    
    def test_cohort_ownership(self):
        cohorts = self.session\
            .query(Cohort)\
            .join(CohortUser)\
            .join(User)\
            .filter(CohortUser.role == CohortUserRole.OWNER)\
            .filter(User.username == 'Evan')\
            .all()
        print cohorts
        assert_equal(len(cohorts), 2, "User Evan should own 2 cohorts")
