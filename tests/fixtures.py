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
    PersistentReport,
    Revision,
    Page,
    MediawikiUser,
    Logging,
)


class DatabaseTest(unittest.TestCase):
    
    def runTest(self):
        pass
    
    def setUp(self):
        
        #****************************************************************
        # set up for every test - delete and re-create all needed records
        #****************************************************************
        project = 'enwiki'
        self.session = db.get_session()
        engine = db.get_mw_engine(project)
        db.MediawikiBase.metadata.create_all(engine, checkfirst=True)
        self.mwSession = db.get_mw_session(project)
        DatabaseTest.tearDown(self)
        
        #****************************************************************
        # create records for enwiki tests
        #****************************************************************
        mw_user_dan = MediawikiUser(user_name='Dan')
        mw_user_evan = MediawikiUser(user_name='Evan')
        mw_user_andrew = MediawikiUser(user_name='Andrew')
        mw_user_diederik = MediawikiUser(user_name='Diederik')
        mw_logging = Logging(log_user_text='Reedy')
        mw_page = Page(page_namespace=0, page_title='Main_Page')
        mw_second_page = Page(page_namespace=209, page_title='Page in Namespace 209')
        self.mwSession.add_all([
            mw_user_dan,
            mw_user_evan,
            mw_user_andrew,
            mw_logging,
            mw_page,
            mw_second_page,
        ])
        self.mwSession.commit()
        
        # edits in between Dan and Evan edits
        rev_before_1 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_diederik.user_id,
            rev_comment='before Dan edit 1',
            rev_len=4, rev_timestamp=datetime(2013, 05, 30),
        )
        rev_before_2 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_diederik.user_id,
            rev_comment='before Dan edit 2',
            rev_len=0, rev_timestamp=datetime(2013, 06, 30),
        )
        rev_before_3 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_diederik.user_id,
            rev_comment='before Evan edit 1',
            rev_len=0, rev_timestamp=datetime(2013, 05, 30),
        )
        rev_before_4 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_diederik.user_id,
            rev_comment='before Evan edit 2',
            rev_len=100, rev_timestamp=datetime(2013, 06, 30),
        )
        rev_before_5 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_diederik.user_id,
            rev_comment='before Evan edit 3',
            rev_len=140, rev_timestamp=datetime(2013, 07, 23),
        )
        rev_alternate_namespace_1 = Revision(
            rev_page=mw_second_page.page_id, rev_user=mw_user_dan.user_id,
            rev_comment='first revision in namespace 209',
            # NOTE: VIM is freaking out if I type 08 below.  Is this true on Mac?
            rev_len=100, rev_timestamp=datetime(2013, 8, 5),
        )
        self.mwSession.add_all([
            rev_before_1,
            rev_before_2,
            rev_before_3,
            rev_before_4,
            rev_before_5,
            rev_alternate_namespace_1,
        ])
        self.mwSession.commit()
        
        # Dan edits
        rev1 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_dan.user_id,
            rev_comment='Dan edit 1', rev_parent_id=rev_before_1.rev_id,
            rev_len=0, rev_timestamp=datetime(2013, 06, 01),
        )
        rev2 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_dan.user_id,
            rev_comment='Dan edit 2', rev_parent_id=rev_before_2.rev_id,
            rev_len=10, rev_timestamp=datetime(2013, 07, 01),
        )
        # Evan edits
        rev3 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_evan.user_id,
            rev_comment='Evan edit 1', rev_parent_id=rev_before_3.rev_id,
            rev_len=100, rev_timestamp=datetime(2013, 06, 01),
        )
        rev4 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_evan.user_id,
            rev_comment='Evan edit 2', rev_parent_id=rev_before_4.rev_id,
            rev_len=140, rev_timestamp=datetime(2013, 07, 01),
        )
        rev5 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_evan.user_id,
            rev_comment='Evan edit 3', rev_parent_id=rev_before_5.rev_id,
            rev_len=136, rev_timestamp=datetime(2013, 07, 24),
        )
        self.mwSession.add_all([rev1, rev2, rev3, rev4, rev5])
        self.mwSession.commit()
        
        #****************************************************************
        # create basic test records for non-mediawiki tests
        #****************************************************************
        dan_user = User(username='Dan')
        evan_user = User(username='Evan')
        web_test_user = User(email='test@test.com')
        
        # create a test cohort
        dan = WikiUser(
            mediawiki_username=mw_user_dan.user_name,
            mediawiki_userid=mw_user_dan.user_id,
            project=project
        )
        evan = WikiUser(
            mediawiki_username=mw_user_evan.user_name,
            mediawiki_userid=mw_user_evan.user_id,
            project=project
        )
        andrew = WikiUser(
            mediawiki_username=mw_user_andrew.user_name,
            mediawiki_userid=mw_user_andrew.user_id,
            project=project
        )
        diederik = WikiUser(
            mediawiki_username=mw_user_diederik.user_name,
            mediawiki_userid=mw_user_diederik.user_id,
            project=project
        )
        
        # create cohorts
        test_cohort = Cohort(name='test', enabled=True, public=False)
        private_cohort = Cohort(name='test_private', enabled=True, public=False)
        private_cohort2 = Cohort(name='test_private2', enabled=True, public=False)
        disabled_cohort = Cohort(name='test_disabled', enabled=False, public=False)
        self.session.add_all([
            #report,
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
        diederik_in_test = CohortWikiUser(
            wiki_user_id=diederik.id,
            cohort_id=test_cohort.id
        )
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
        
        # add reports
        report_created = PersistentReport(
            user_id=web_test_user.id,
            status=celery.states.PENDING,
            queue_result_key=None,
            show_in_ui=True
        )
        report_started = PersistentReport(
            user_id=web_test_user.id,
            status=celery.states.STARTED,
            queue_result_key=None,
            show_in_ui=True
        )
        report_started2 = PersistentReport(
            user_id=web_test_user.id,
            status=celery.states.STARTED,
            queue_result_key=None,
            show_in_ui=True
        )
        report_finished = PersistentReport(
            user_id=web_test_user.id,
            status=celery.states.SUCCESS,
            queue_result_key=None,
            show_in_ui=True
        )
        self.session.add_all([
            report_created,
            report_started,
            report_started2,
            report_finished
        ])
        self.session.commit()
        
        #****************************************************************
        # keep the test ids around so subclasses can use them
        #****************************************************************
        self.test_report_id = report_created.id
        self.test_user_id = dan_user.id
        self.test_web_user_id = web_test_user.id
        self.test_cohort_id = test_cohort.id
        self.test_cohort_user_id = dan_owns_test.id
        self.test_wiki_user_id = dan.id
        self.test_cohort_wiki_user_id = dan_in_test.id
        self.test_logging_id = mw_logging.log_id
        self.test_mediawiki_user_id = mw_user_dan.user_id
        self.test_mediawiki_user_id_evan = mw_user_evan.user_id
        self.test_mediawiki_user_id_andrew = mw_user_andrew.user_id
        self.test_mediawiki_user_id_diederik = mw_user_diederik.user_id
        self.test_page_id = mw_page.page_id
        self.test_revision_id = rev1.rev_id
    
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
        self.session.query(PersistentReport).delete()
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


class WebTestAnonymous(DatabaseTest):
    """
    Creates a test flask client but does not authenticate.
    """
    
    def setUp(self):
        """
        Creates a test flask environment.
        Logs in a test user so tests on private urls work.
        """
        DatabaseTest.setUp(self)
        self.app = app.test_client()
    
    def tearDown(self):
        DatabaseTest.tearDown(self)


class WebTest(WebTestAnonymous):
    """
    Creates a test flask client from the normally configured app.
    Makes sure that a user is authenticated as far as Flask-Login is concerned,
    so that any private routes are still served for testing purposes.
    """
    
    def setUp(self):
        """
        Creates a test flask environment.
        Logs in a test user so tests on private urls work.
        """
        WebTestAnonymous.setUp(self)
        self.app.get('/login-for-testing-only')
    
    def tearDown(self):
        WebTestAnonymous.tearDown(self)
        self.app.get('/logout')


class DatabaseWithCohortTest(DatabaseTest):
    
    def setUp(self):
        DatabaseTest.setUp(self)
        self.cohort = self.session.query(Cohort).filter_by(name='test').one()
        wikiusers = self.session.query(WikiUser)\
            .join(CohortWikiUser)\
            .filter(CohortWikiUser.cohort_id == self.cohort.id)
        
        self.dan_id = wikiusers\
            .filter(WikiUser.mediawiki_username == 'Dan')\
            .one().mediawiki_userid
        self.evan_id = wikiusers\
            .filter(WikiUser.mediawiki_username == 'Evan')\
            .one().mediawiki_userid
        self.andrew_id = wikiusers\
            .filter(WikiUser.mediawiki_username == 'Andrew')\
            .one().mediawiki_userid
        self.diederik_id = wikiusers\
            .filter(WikiUser.mediawiki_username == 'Diederik')\
            .one().mediawiki_userid
