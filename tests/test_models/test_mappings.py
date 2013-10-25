from nose.tools import assert_true, assert_equal
import celery
from wikimetrics.models import (
    PersistentReport,
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
    """
    Mapping tests for our custom tables
    """
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_report(self):
        pr = PersistentReport(status=celery.states.PENDING)
        self.session.add(pr)
        self.session.commit()
        row = self.session.query(PersistentReport).get(pr.id)
        assert_equal(row.status, celery.states.PENDING)
    
    def test_user(self):
        u = self.session.query(User).get(self.owner_user_id)
        assert_equal(u.username, 'test cohort owner')
        assert_equal(u.role, UserRole.GUEST)
    
    def test_wikiuser(self):
        wu = self.session.query(WikiUser).filter(
            WikiUser.mediawiki_userid == self.editors[0].user_id
        ).one()
        assert_equal(wu.mediawiki_username, 'Editor test-specific-0')
    
    def test_cohort(self):
        c = self.session.query(Cohort).get(self.cohort.id)
        assert_equal(c.name, 'test-specific-cohort')
        assert_true(c.public is False)
    
    def test_cohort_user(self):
        cu = self.session.query(CohortUser).first()
        assert_equal(cu.user_id, self.owner_user_id)
        assert_equal(cu.cohort_id, self.cohort.id)
    
    def test_cohort_wikiuser(self):
        cwu = self.session.query(CohortWikiUser).all()[0]
        assert_equal(cwu.cohort_id, self.cohort.id)
    
    #***********
    # Mapping tests for mediawiki tables
    #***********
    def test_mediawiki_logging(self):
        l = Logging(log_user_text='Reedy')
        self.mwSession.add(l)
        self.mwSession.commit()
        row = self.mwSession.query(Logging).get(l.log_id)
        assert_equal(row.log_user_text, 'Reedy')
    
    def test_mediawiki_user(self):
        row = self.mwSession.query(MediawikiUser).get(self.editors[0].user_id)
        assert_equal(row.user_name, 'Editor test-specific-0')
    
    def test_mediawiki_page(self):
        row = self.mwSession.query(Page).get(self.revisions[0].rev_page)
        assert_equal(row.page_title, 'test-specific-page')
    
    def test_mediawiki_revision(self):
        row = self.mwSession.query(Revision).get(self.revisions[0].rev_id)
        assert_equal(row.rev_comment, 'revision 0, editor 0')
    
    #***********
    # Join tests
    #***********
    def test_cohort_members(self):
        user_ids = self.session\
            .query(WikiUser.mediawiki_userid)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == self.cohort.id)\
            .all()
        assert_equal(len(user_ids), 4)
    
    def test_cohort_ownership(self):
        cohorts = self.session\
            .query(Cohort)\
            .join(CohortUser)\
            .join(User)\
            .filter(CohortUser.role == CohortUserRole.OWNER)\
            .filter(User.username == 'test cohort owner')\
            .all()
        assert_equal(len(cohorts), 1)
    
    #***********
    # String representation tests
    #***********
    def test_report_repr(self):
        pr = PersistentReport(status=celery.states.PENDING)
        self.session.add(pr)
        self.session.commit()
        row = self.session.query(PersistentReport).get(pr.id)
        assert_true(str(row).find('PersistentReport') >= 0)
    
    def test_user_repr(self):
        u = self.session.query(User).first()
        assert_true(str(u).find('User') >= 0)
    
    def test_cohort_repr(self):
        c = self.session.query(Cohort).first()
        assert_true(str(c).find('Cohort') >= 0)
    
    def test_cohort_user_repr(self):
        cu = self.session.query(CohortUser).first()
        assert_true(str(cu).find('CohortUser') >= 0)
    
    def test_wikiuser_repr(self):
        wu = self.session.query(WikiUser).first()
        assert_true(str(wu).find('WikiUser') >= 0)
    
    def test_cohort_wikiuser_repr(self):
        cwu = self.session.query(CohortWikiUser).first()
        assert_true(str(cwu).find('CohortWikiUser') >= 0)
