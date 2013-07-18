import unittest
import celery
from datetime import datetime

__all__ = [
    'DatabaseTest',
    'DatabaseWithCohortTest',
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
    PersistentJob,
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
        self.mwSession = db.get_mw_session('enwiki')
        DatabaseTest.tearDown(self)
        
        dan_user = User(username='Dan')
        evan_user = User(username='Evan')
        web_test_user = User(email='test@test.com')
        
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
            #job,
            dan_user,
            evan_user,
            web_test_user,
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
        web_user_owns_test = CohortUser(
            user_id=web_test_user.id,
            cohort_id=test_cohort.id,
            role=CohortUserRole.OWNER,
        )
        web_user_owns_private = CohortUser(
            user_id=web_test_user.id,
            cohort_id=private_cohort.id,
            role=CohortUserRole.OWNER,
        )
        web_user_owns_private2 = CohortUser(
            user_id=web_test_user.id,
            cohort_id=private_cohort2.id,
            role=CohortUserRole.OWNER,
        )
        dan_views_private2 = CohortUser(
            user_id=dan_user.id,
            cohort_id=private_cohort2.id,
            role=CohortUserRole.VIEWER
        )
        self.session.add_all([
            dan_owns_test,
            evan_owns_private,
            evan_owns_private2,
            web_user_owns_test,
            web_user_owns_private,
            web_user_owns_private2,
            dan_views_private2
        ])
        self.session.commit()
        
        # add jobs
        job_created = PersistentJob(
            user_id=web_test_user.id,
            status=celery.states.PENDING,
            result_key=None,
            show_in_ui=True
        )
        job_started = PersistentJob(
            user_id=web_test_user.id,
            status=celery.states.STARTED,
            result_key=None,
            show_in_ui=True
        )
        job_started2 = PersistentJob(
            user_id=web_test_user.id,
            status=celery.states.STARTED,
            result_key=None,
            show_in_ui=True
        )
        job_finished = PersistentJob(
            user_id=web_test_user.id,
            status=celery.states.SUCCESS,
            result_key=None,
            show_in_ui=True
        )
        self.session.add_all([
            job_created,
            job_started,
            job_started2,
            job_finished
        ])
        self.session.commit()
        
        # create records for enwiki tests
        # TODO: make this safe to execute in any environment
        self.mwSession.add(MediawikiUser(user_id=1, user_name='Dan'))
        self.mwSession.add(MediawikiUser(user_id=2, user_name='Evan'))
        self.mwSession.add(MediawikiUser(user_id=3, user_name='Andrew'))
        self.mwSession.add(Logging(log_id=1, log_user_text='Reedy'))
        self.mwSession.add(Page(page_id=1, page_namespace=0, page_title='Main_Page'))
        # edits in between Dan and Evan edits
        self.mwSession.add(Revision(
            rev_id=1, rev_page=1, rev_user=4, rev_comment='before Dan edit 1',
            rev_len=4, rev_timestamp=datetime(2013, 05, 30),
        ))
        self.mwSession.add(Revision(
            rev_id=3, rev_page=1, rev_user=4, rev_comment='before Dan edit 2',
            rev_len=0, rev_timestamp=datetime(2013, 06, 30),
        ))
        self.mwSession.add(Revision(
            rev_id=5, rev_page=1, rev_user=4, rev_comment='before Evan edit 1',
            rev_len=0, rev_timestamp=datetime(2013, 05, 30),
        ))
        self.mwSession.add(Revision(
            rev_id=7, rev_page=1, rev_user=4, rev_comment='before Evan edit 2',
            rev_len=100, rev_timestamp=datetime(2013, 06, 30),
        ))
        self.mwSession.add(Revision(
            rev_id=9, rev_page=1, rev_user=4, rev_comment='before Evan edit 3',
            rev_len=140, rev_timestamp=datetime(2013, 07, 23),
        ))
        # Dan edits
        self.mwSession.add(Revision(
            rev_id=2, rev_page=1, rev_user=1, rev_comment='Dan edit 1',
            rev_parent_id=1, rev_len=0, rev_timestamp=datetime(2013, 06, 01),
        ))
        self.mwSession.add(Revision(
            rev_id=4, rev_page=1, rev_user=1, rev_comment='Dan edit 2',
            rev_parent_id=3, rev_len=10, rev_timestamp=datetime(2013, 07, 01),
        ))
        # Evan edits
        self.mwSession.add(Revision(
            rev_id=6, rev_page=1, rev_user=2, rev_comment='Evan edit 1',
            rev_parent_id=5, rev_len=100, rev_timestamp=datetime(2013, 06, 01),
        ))
        self.mwSession.add(Revision(
            rev_id=8, rev_page=1, rev_user=2, rev_comment='Evan edit 2',
            rev_parent_id=7, rev_len=140, rev_timestamp=datetime(2013, 07, 01),
        ))
        self.mwSession.add(Revision(
            rev_id=10, rev_page=1, rev_user=2, rev_comment='Evan edit 3',
            rev_parent_id=9, rev_len=136, rev_timestamp=datetime(2013, 07, 24),
        ))
        self.mwSession.commit()
    
    def tearDown(self):
        
        # delete records
        self.mwSession.query(MediawikiUser).delete()
        self.mwSession.query(Logging).delete()
        self.mwSession.query(Page).delete()
        self.mwSession.query(Revision).delete()
        self.mwSession.commit()
        self.mwSession.close()
        
        self.session.query(CohortWikiUser).delete()
        self.session.query(CohortUser).delete()
        self.session.query(WikiUser).delete()
        self.session.query(Cohort).delete()
        self.session.query(User).delete()
        self.session.query(PersistentJob).delete()
        self.session.commit()
        self.session.close()


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


class DatabaseWithCohortTest(DatabaseTest):
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.cohort = self.session.query(Cohort).filter_by(name='test').one()
        wikiusers = self.session.query(WikiUser)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == self.cohort.id)
        
        self.dan_id = wikiusers.filter(WikiUser.mediawiki_username == 'Dan').one().id
        self.evan_id = wikiusers.filter(WikiUser.mediawiki_username == 'Evan').one().id
