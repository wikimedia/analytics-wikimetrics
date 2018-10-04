from nose.tools import assert_true, assert_equal, assert_not_equal
import celery
from wikimetrics.models import (
    ReportStore,
    TaskErrorStore,
    UserStore,
    CohortStore,
    CohortUserStore,
    CohortWikiUserStore,
    WikiUserStore,
    Logging,
    Page,
    MediawikiUser,
    MediawikiUserGroups,
    Revision,
    CentralAuthLocalUser
)
from wikimetrics.enums import CohortUserRole, UserRole
from tests.fixtures import DatabaseTest


class TestMappings(DatabaseTest):
    """
    Mapping tests for our custom tables
    """
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.common_cohort_1()
    
    def test_report(self):
        pr = ReportStore(status=celery.states.PENDING)
        self.session.add(pr)
        self.session.commit()
        row = self.session.query(ReportStore).get(pr.id)
        assert_equal(row.status, celery.states.PENDING)

    def test_task_error(self):
        pr = ReportStore(status=celery.states.PENDING)
        self.session.add(pr)
        self.session.commit()
        te = TaskErrorStore(task_type='report', task_id=pr.id,
                            message='m', traceback='t', count=1)
        self.session.add(te)
        self.session.commit()
        row = self.session.query(TaskErrorStore).first()
        assert_equal(row.task_type, 'report')
        assert_equal(row.task_id, pr.id)
        assert_equal(row.message, 'm')
        assert_equal(row.traceback, 't')
        assert_equal(row.count, 1)
    
    def test_user(self):
        u = self.session.query(UserStore).get(self.owner_user_id)
        assert_equal(u.username, 'test cohort owner')
        assert_equal(u.role, UserRole.GUEST)
    
    def test_wikiuser(self):
        wu = self.session.query(WikiUserStore).filter(
            WikiUserStore.mediawiki_userid == self.editors[0].user_id
        ).one()
        assert_equal(wu.mediawiki_username, 'Editor test-specific-0')
    
    def test_cohort(self):
        c = self.session.query(CohortStore).get(self.cohort.id)
        assert_equal(c.name, 'test-specific-cohort')
        assert_true(c.public is False)
    
    def test_cohort_user(self):
        cu = self.session.query(CohortUserStore).first()
        assert_equal(cu.user_id, self.owner_user_id)
        assert_equal(cu.cohort_id, self.cohort.id)
    
    def test_cohort_wikiuser(self):
        cwu = self.session.query(CohortWikiUserStore).all()[0]
        assert_equal(cwu.cohort_id, self.cohort.id)
    
    #***********
    # Mapping tests for mediawiki tables
    #***********
    def test_mediawiki_logging(self):
        logging = Logging(log_user_text='Reedy', log_user=self.editors[0].user_id)
        self.mwSession.add(logging)
        self.mwSession.commit()
        row = self.mwSession.query(Logging).get(logging.log_id)
        assert_equal(row.log_user_text, 'Reedy')
    
    def test_mediawiki_user(self):
        row = self.mwSession.query(MediawikiUser).get(self.editors[0].user_id)
        assert_equal(row.user_name, 'Editor test-specific-0')
    
    def test_mediawiki_user_groups(self):
        ug = MediawikiUserGroups(ug_user=self.editors[0].user_id, ug_group='test')
        self.mwSession.add(ug)
        self.mwSession.commit()
        fetch = self.mwSession.query(MediawikiUserGroups).first()
        assert_equal(fetch.ug_group, 'test')
    
    def test_mediawiki_page(self):
        row = self.mwSession.query(Page).get(self.revisions[0].rev_page)
        assert_equal(row.page_title, 'test-specific-page')
    
    def test_mediawiki_revision(self):
        row = self.mwSession.query(Revision).get(self.revisions[0].rev_id)
        assert_equal(row.rev_comment, 'revision 0, editor 0')

    #***********
    # Mapping tests for centralauth tables
    #***********
    def test_centralauth_localuser(self):
        row = self.caSession.query(CentralAuthLocalUser).first()
        assert_equal(row.lu_name, 'Editor test-specific-0')

    #***********
    # Join tests
    #***********
    def test_cohort_members(self):
        user_ids = self.session\
            .query(WikiUserStore.mediawiki_userid)\
            .join(CohortWikiUserStore)\
            .filter(CohortWikiUserStore.cohort_id == self.cohort.id)\
            .all()
        assert_equal(len(user_ids), 4)
    
    def test_cohort_ownership(self):
        cohorts = self.session\
            .query(CohortStore)\
            .join(CohortUserStore)\
            .join(UserStore)\
            .filter(CohortUserStore.role == CohortUserRole.OWNER)\
            .filter(UserStore.username == 'test cohort owner')\
            .all()
        assert_equal(len(cohorts), 1)
    
    #***********
    # String representation tests
    #***********
    def test_report_repr(self):
        pr = ReportStore(status=celery.states.PENDING)
        self.session.add(pr)
        self.session.commit()
        row = self.session.query(ReportStore).get(pr.id)
        assert_true(str(row).find('ReportStore') >= 0)

    def test_task_error_repr(self):
        pr = ReportStore(status=celery.states.PENDING)
        self.session.add(pr)
        self.session.commit()
        te = TaskErrorStore(task_type='report', task_id=pr.id,
                            message='m', traceback='t', count=1)
        self.session.add(te)
        self.session.commit()
        row = self.session.query(TaskErrorStore).first()
        assert_true(str(row).find('TaskErrorStore') >= 0)
    
    def test_user_repr(self):
        u = self.session.query(UserStore).first()
        assert_true(str(u).find('User') >= 0)
    
    def test_cohort_repr(self):
        c = self.session.query(CohortStore).first()
        assert_true(str(c).find('Cohort') >= 0)
    
    def test_cohort_user_repr(self):
        cu = self.session.query(CohortUserStore).first()
        assert_true(str(cu).find('CohortUser') >= 0)
    
    def test_wikiuser_repr(self):
        wu = self.session.query(WikiUserStore).first()
        assert_true(str(wu).find('WikiUser') >= 0)
    
    def test_cohort_wikiuser_repr(self):
        cwu = self.session.query(CohortWikiUserStore).first()
        assert_true(str(cwu).find('CohortWikiUser') >= 0)
