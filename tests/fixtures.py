import unittest

__all__ = [
    'DatabaseTest',
    'QueueTest',
    'QueueDatabaseTest',
    'WebTest',
]


from wikimetrics.configurables import db
from wikimetrics.models import (
    User,
    WikiUser,
    Cohort,
    CohortWikiUser,
    CohortUserRole,
    CohortUser,
    Job,
    JobStatus,
    Revision,
    Page,
    MediawikiUser,
    Logging,
)


class DatabaseTest(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def setUp(self):
        
        # create basic test records for non-mediawiki tests
        self.session = db.get_session()
        
        job = Job()
        dan_user = User(username='Dan')
        evan_user = User(username='Evan')
        
        # create a test cohort
        dan = WikiUser(mediawiki_username='Dan', mediawiki_userid=1, project='enwiki')
        evan = WikiUser(mediawiki_username='Evan', mediawiki_userid=2, project='enwiki')
        andrew = WikiUser(mediawiki_username='Andrew', mediawiki_userid=3, project='enwiki')
        diederik = WikiUser(mediawiki_username='Diederik', mediawiki_userid=4, project='enwiki')
        
        # create cohorts
        test_cohort = Cohort(name='test', enabled=True, public=True)
        private_cohort = Cohort(name='test_private', enabled=True, public=False)
        private_cohort2 = Cohort(name='test_private2', enabled=True, public=False)
        disabled_cohort = Cohort(name='test_disabled', enabled=False, public=True)
        self.session.add_all([
            job,
            dan_user,
            evan_user,
            dan,
            evan,
            andrew,
            diederik,
            test_cohort,
            private_cohort,
            private_cohort2,
            disabled_cohort])
        self.session.commit()
        
        # create cohort membership
        dan_in_test = CohortWikiUser(wiki_user_id=dan.id, cohort_id=test_cohort.id)
        evan_in_test = CohortWikiUser(wiki_user_id=evan.id, cohort_id=test_cohort.id)
        andrew_in_test = CohortWikiUser(wiki_user_id=andrew.id, cohort_id=test_cohort.id)
        diederik_in_test = CohortWikiUser(wiki_user_id=diederik.id, cohort_id=test_cohort.id)
        self.session.add_all([
            dan_in_test,
            evan_in_test,
            andrew_in_test,
            diederik_in_test
        ])
        self.session.commit()
        
        # create cohort ownership
        dan_owns_test = CohortUser(
            user_id=dan_user.id,
            cohort_id=test_cohort.id,
            role=CohortUserRole.OWNER,
        )
        evan_owns_private = CohortUser(
            user_id=evan_user.id,
            cohort_id=private_cohort.id,
            role=CohortUserRole.OWNER,
        )
        evan_owns_private2 = CohortUser(
            user_id=evan_user.id,
            cohort_id=private_cohort2.id,
            role=CohortUserRole.OWNER,
        )
        dan_views_private2 = CohortUser(
            user_id=evan_user.id,
            cohort_id=private_cohort2.id,
            role=CohortUserRole.VIEWER
        )
        self.session.add_all([
            dan_owns_test,
            evan_owns_private,
            evan_owns_private2,
            dan_views_private2
        ])
        self.session.commit()
        
        # add jobs
        job_created = Job(user_id=2, classpath='', status=JobStatus.CREATED, result_id=None)
        job_started = Job(user_id=2, classpath='', status=JobStatus.STARTED, result_id=None)
        job_started2 = Job(user_id=2, classpath='', status=JobStatus.STARTED, result_id=None)
        job_finished = Job(user_id=2, classpath='', status=JobStatus.FINISHED, result_id=None)
        self.session.add_all([
            job_created,
            job_started,
            job_started2,
            job_finished
        ])
        self.session.commit()
        
        self.mwSession = db.get_mw_session('enwiki')
        
        # create records for enwiki tests
        self.mwSession.add(MediawikiUser(user_id=1, user_name='Dan'))
        self.mwSession.add(MediawikiUser(user_id=2, user_name='Evan'))
        self.mwSession.add(MediawikiUser(user_id=3, user_name='Andrew'))
        self.mwSession.add(Logging(log_id=1, log_user_text='Reedy'))
        self.mwSession.add(Page(page_id=1, page_namespace=0, page_title='Main_Page'))
        # Dan edits
        self.mwSession.add(Revision(rev_id=1, rev_page=1, rev_user=1, rev_comment='Dan edit 1'))
        self.mwSession.add(Revision(rev_id=2, rev_page=1, rev_user=1, rev_comment='Dan edit 2'))
        # Evan edits
        self.mwSession.add(Revision(rev_id=3, rev_page=1, rev_user=2, rev_comment='Evan edit 1'))
        self.mwSession.add(Revision(rev_id=4, rev_page=1, rev_user=2, rev_comment='Evan edit 2'))
        self.mwSession.add(Revision(rev_id=5, rev_page=1, rev_user=2, rev_comment='Evan edit 3'))
        self.mwSession.commit()
    
    def tearDown(self):
        
        # delete records
        self.mwSession.query(MediawikiUser).delete()
        self.mwSession.query(Logging).delete()
        self.mwSession.query(Page).delete()
        self.mwSession.query(Revision).delete()
        self.mwSession.commit()
        
        self.session = db.get_session()
        self.session.query(CohortWikiUser).delete()
        self.session.query(CohortUser).delete()
        self.session.query(WikiUser).delete()
        self.session.query(Cohort).delete()
        self.session.query(User).delete()
        self.session.query(Job).delete()
        self.session.commit()


class QueueTest(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass


class QueueDatabaseTest(QueueTest, DatabaseTest):
    
    def setUp(self):
        QueueTest.setUp(self)
        DatabaseTest.setUp(self)
    
    def tearDown(self):
        QueueTest.tearDown(self)
        DatabaseTest.tearDown(self)


from wikimetrics.configurables import app
from flask.ext.login import login_user, logout_user, current_user


class WebTest(DatabaseTest):
    """
    Creates a test flask client from the normally configured app.
    Makes sure that a user is authenticated as far as Flask-Login is concerned,
    so that any private routes are still served for testing purposes.
    """
    
    def setUp(self):
        """
        Creates a test flask environment.  Logs in a test user so tests on private urls work.
        """
        DatabaseTest.setUp(self)
        self.app = app.test_client()
        self.app.get('/login-for-testing-only')
    
    def tearDown(self):
        DatabaseTest.tearDown(self)
        self.app.get('/logout')
