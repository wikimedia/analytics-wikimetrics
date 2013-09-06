import unittest
import celery
import sys
from datetime import datetime
from nose.tools import nottest

__all__ = [
    'DatabaseTest',
    'DatabaseWithCohortTest',
    'DatabaseWithSurvivorCohortTest',
    'DatabaseForPagesCreatedTest',
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
    """
    WARNING: making instance methods on test classes is ok, but you
             MUST decorate them as @nottest otherwise they will execute
             as part of test runs
    """
    
    def runTest(self):
        pass
    
    @nottest
    def create_test_cohort(
        self,
        name='test-specific',
        editor_count=0,
        revisions_per_editor=0,
        revision_timestamps=[],
        revision_lengths=[],
    ):
        """
        Parameters
            name                    : a unique name to append to everything
            editor_count            : count of editors we want in this cohort
            revisions_per_editor    : count of revisions we want for each editor
            revision_timestamps     : two dimensional array indexed by
                                        editor from 0 to editor_count-1
                                        revision from 0 to revisions_per_editor-1
            revision_lengths        : two dimensional array indexed same as above OR
                                        a single integer so all revisions will
                                        have the same length
        
        Returns
            Nothing but creates the following, to be accessed in a test:
              self.cohort       : owned by web_test_user, contains self.editors
              self.page         : the page that all the editors edited
              self.editors      : the mediawiki editors from the cohort
              self.revisions    : the revisions added, in a two dimensional array
        """
        if type(revision_lengths) is int:
            revision_lengths = [[revision_lengths] * revisions_per_editor] * editor_count
        
        self.project = 'enwiki'
        self.editors = []
        self.revisions = []
        
        self.cohort = Cohort(name='{0}-cohort'.format(name), enabled=True, public=False)
        self.session.add(self.cohort)
        self.session.commit()
        
        self.page = Page(page_namespace=0, page_title='{0}-page'.format(name))
        self.mwSession.add(self.page)
        self.mwSession.commit()
        
        for e in range(editor_count):
            editor = MediawikiUser(user_name='Editor {0}-{1}'.format(name, e))
            self.mwSession.add(editor)
            self.mwSession.commit()
            self.editors.append(editor)
            
            wiki_editor = WikiUser(
                mediawiki_username=editor.user_name,
                mediawiki_userid=editor.user_id,
                project=self.project,
            )
            self.session.add(wiki_editor)
            self.session.commit()
            
            cohort_wiki_editor = CohortWikiUser(
                cohort_id=self.cohort.id,
                wiki_user_id=wiki_editor.id,
            )
            self.session.add(cohort_wiki_editor)
            self.session.commit()
            
            for r in range(revisions_per_editor):
                revision = Revision(
                    rev_page=self.page.page_id,
                    rev_user=editor.user_id,
                    rev_comment='revision {0}, editor {1}'.format(r, e),
                    rev_timestamp=revision_timestamps[e][r],
                    rev_len=revision_lengths[e][r],
                    # rev_parent_id will be set below, following chronology
                )
                self.revisions.append(revision)
        
        self.mwSession.add_all(self.revisions)
        self.mwSession.commit()
        # add rev_parent_id chain in chronological order
        ordered_revisions = sorted(self.revisions, key=lambda r: r.rev_timestamp)
        for i, revision in enumerate(ordered_revisions):
            if i == 0:
                revision.rev_parent_id = 0
            else:
                revision.rev_parent_id = ordered_revisions[i - 1].rev_id
        
        self.mwSession.commit()
    
    # create test data for metric PagesCreated
    @nottest
    def createTestDataMetricPagesCreated(self, user, second_user):
        mw_page_evan1 = Page(page_namespace=301, page_title='Page1')
        mw_page_evan2 = Page(page_namespace=302, page_title='Page2')
        mw_page_evan3 = Page(page_namespace=303, page_title='Page3')
        mw_page_dan1 = Page(page_namespace=301, page_title='Page4')
        self.mwSession.add_all(
            [mw_page_evan1, mw_page_evan2, mw_page_evan3, mw_page_dan1]
        )
        self.mwSession.commit()
        revisions = []

        r1 = None
        r2 = None
        r3 = None
        r4 = None
        for i in range(0, 3):
            parent_id1 = (0 if r1 is None else r1.rev_id)
            parent_id2 = (0 if r2 is None else r2.rev_id)
            parent_id3 = (0 if r3 is None else r3.rev_id)
            parent_id4 = (0 if r4 is None else r4.rev_id)
            r1 = Revision(
                rev_page=mw_page_evan1.page_id,
                rev_user=user.user_id,
                rev_comment='Evan edit ' + str(i),
                rev_parent_id=parent_id1,
                rev_len=100,
                rev_timestamp=20130620000000,
            )
            r2 = Revision(
                rev_page=mw_page_evan1.page_id,
                rev_user=user.user_id,
                rev_comment='Evan edit ' + str(i),
                rev_parent_id=parent_id2,
                rev_len=100,
                rev_timestamp=20130720000000,
            )
            r3 = Revision(
                rev_page=mw_page_evan1.page_id,
                rev_user=user.user_id,
                rev_comment='Evan edit ' + str(i),
                rev_parent_id=parent_id3,
                rev_len=100,
                rev_timestamp=20130820000000,
            )
            r4 = Revision(
                rev_page=mw_page_dan1.page_id,
                rev_user=second_user.user_id,
                rev_comment='Dan edit ' + str(i),
                rev_parent_id=parent_id4,
                rev_len=100,
                rev_timestamp=20130820000000,
            )
            revisions.append([r1, r2, r3, r4])
            self.mwSession.add_all([r1, r2, r3, r4])
            self.mwSession.commit()
    
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
            rev_len=4, rev_timestamp=20130530000000,
        )
        rev_before_2 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_diederik.user_id,
            rev_comment='before Dan edit 2',
            rev_len=0, rev_timestamp=20130630000000,
        )
        rev_before_3 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_diederik.user_id,
            rev_comment='before Evan edit 1',
            rev_len=0, rev_timestamp=20130530000000,
        )
        rev_before_4 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_diederik.user_id,
            rev_comment='before Evan edit 2',
            rev_len=100, rev_timestamp=20130630000000,
        )
        rev_before_5 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_diederik.user_id,
            rev_comment='before Evan edit 3',
            rev_len=140, rev_timestamp=20130723000000,
        )
        rev_alternate_namespace_1 = Revision(
            rev_page=mw_second_page.page_id, rev_user=mw_user_dan.user_id,
            rev_comment='first revision in namespace 209',
            # NOTE: VIM is freaking out if I type 08 below.  Is this true on Mac?
            rev_len=100, rev_timestamp=20130805000000,
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
            rev_len=0, rev_timestamp=20130601000000,
        )
        rev2 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_dan.user_id,
            rev_comment='Dan edit 2', rev_parent_id=rev_before_2.rev_id,
            rev_len=10, rev_timestamp=20130701000000,
        )
        # Evan edits
        rev3 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_evan.user_id,
            rev_comment='Evan edit 1', rev_parent_id=rev_before_3.rev_id,
            rev_len=100, rev_timestamp=20130601000000,
        )
        rev4 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_evan.user_id,
            rev_comment='Evan edit 2', rev_parent_id=rev_before_4.rev_id,
            rev_len=140, rev_timestamp=20130701000000,
        )
        rev5 = Revision(
            rev_page=mw_page.page_id, rev_user=mw_user_evan.user_id,
            rev_comment='Evan edit 3', rev_parent_id=rev_before_5.rev_id,
            rev_len=136, rev_timestamp=20130724000000,
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
        self.test_cohort_name = test_cohort.name
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
        self.mwSession.query(Logging).delete()
        self.mwSession.query(Revision).delete()
        self.mwSession.query(MediawikiUser).delete()
        self.mwSession.query(Page).delete()
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


# class used to test Pages Created metric
class DatabaseForPagesCreatedTest(DatabaseWithCohortTest):

    # create test data for metric PagesCreated
    def createTestDataMetricPagesCreated(self):
        mw_page_evan1 = Page(page_namespace=301, page_title='Page1')
        mw_page_evan2 = Page(page_namespace=302, page_title='Page2')
        mw_page_evan3 = Page(page_namespace=303, page_title='Page3')
        mw_page_dan1 = Page(page_namespace=301, page_title='Page4')
        self.mwSession.add_all(
            [mw_page_evan1, mw_page_evan2, mw_page_evan3, mw_page_dan1]
        )
        self.mwSession.commit()
        revisions = []

        r1 = None
        r2 = None
        r3 = None
        r4 = None
        for i in range(0, 3):
            parent_id1 = (0 if r1 is None else r1.rev_id)
            parent_id2 = (0 if r2 is None else r2.rev_id)
            parent_id3 = (0 if r3 is None else r3.rev_id)
            parent_id4 = (0 if r4 is None else r4.rev_id)
            print("rev_id1=" + str(parent_id1) + "\n", sys.stderr)
            r1 = Revision(
                rev_page=mw_page_evan1.page_id,
                rev_user=self.evan_id,
                rev_comment='Evan edit ' + str(i),
                rev_parent_id=parent_id1,
                rev_len=100,
                rev_timestamp=datetime(2013, 6, 20)
            )
            r2 = Revision(
                rev_page=mw_page_evan1.page_id,
                rev_user=self.evan_id,
                rev_comment='Evan edit ' + str(i),
                rev_parent_id=parent_id2,
                rev_len=100,
                rev_timestamp=datetime(2013, 7, 20)
            )
            r3 = Revision(
                rev_page=mw_page_evan1.page_id,
                rev_user=self.evan_id,
                rev_comment='Evan edit ' + str(i),
                rev_parent_id=parent_id3,
                rev_len=100,
                rev_timestamp=datetime(2013, 8, 20)
            )
            r4 = Revision(
                rev_page=mw_page_dan1.page_id,
                rev_user=self.dan_id,
                rev_comment='Dan edit ' + str(i),
                rev_parent_id=parent_id4,
                rev_len=100,
                rev_timestamp=datetime(2013, 8, 20)
            )
            revisions.append([r1, r2, r3, r4])
            self.mwSession.add_all([r1, r2, r3, r4])
            self.mwSession.commit()

    def setUp(self):
        DatabaseWithCohortTest.setUp(self)
        self.createTestDataMetricPagesCreated()


class DatabaseWithSurvivorCohortTest(DatabaseWithCohortTest):

    # update dan,evan,andrew,diederik user_registration timestamp
    def updateSurvivorRegistrationData(self):
        registration_date_dan    = datetime.strptime("2013-01-01", "%Y-%m-%d")
        registration_date_evan   = datetime.strptime("2013-01-02", "%Y-%m-%d")
        registration_date_andrew = datetime.strptime("2013-01-03", "%Y-%m-%d")
        self.mwSession.query(MediawikiUser.user_id == self.dan_id) \
            .update({"user_registration": registration_date_dan})
        self.mwSession.query(MediawikiUser.user_id == self.evan_id) \
            .update({"user_registration": registration_date_evan})
        self.mwSession.query(MediawikiUser.user_id == self.andrew_id) \
            .update({"user_registration": registration_date_andrew})

    def createPageForSurvivors(self):
        self.page = Page(page_namespace=304, page_title='SurvivorTestPage')
        self.mwSession.add_all([self.page])
        self.mwSession.commit()

    def createRevisionsForSurvivors(self):

        new_revisions = []

        # create a revision for user with id uid at time t
        def createCustomRevision(uid, t):
            r = Revision(
                rev_page=self.page.page_id,
                rev_user=uid,
                rev_comment='Survivor Revision',
                rev_parent_id=111,
                rev_len=100,
                rev_timestamp=t
            )
            new_revisions.append(r)

        createCustomRevision(self.dan_id, datetime(2013, 1, 1))
        createCustomRevision(self.dan_id, datetime(2013, 1, 2))
        createCustomRevision(self.dan_id, datetime(2013, 1, 3))

        createCustomRevision(self.evan_id, datetime(2013, 1, 2))
        createCustomRevision(self.evan_id, datetime(2013, 1, 3))
        createCustomRevision(self.evan_id, datetime(2013, 1, 4))

        createCustomRevision(self.andrew_id, datetime(2013, 1, 3))
        createCustomRevision(self.andrew_id, datetime(2013, 1, 4))
        createCustomRevision(self.andrew_id, datetime(2013, 1, 5))
        createCustomRevision(self.andrew_id, datetime(2013, 1, 6))

        self.mwSession.add_all(new_revisions)
        self.mwSession.commit()

    def setUp(self):
        DatabaseWithCohortTest.setUp(self)
        self.updateSurvivorRegistrationData()
        self.createPageForSurvivors()
        self.createRevisionsForSurvivors()
