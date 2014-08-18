import unittest
import sys
from itertools import product
from datetime import datetime
from nose.tools import nottest
from mock import Mock
from logging import RootLogger, getLogger

from wikimetrics.utils import (
    parse_date, format_date, parse_pretty_date, format_pretty_date, UNICODE_NULL
)
from wikimetrics.configurables import db
from wikimetrics.models import (
    UserStore,
    WikiUserStore,
    WikiUserKey,
    CohortStore,
    CohortWikiUserStore,
    CohortUserStore,
    TagStore,
    CohortTagStore,
    ReportStore,
    Revision,
    Page,
    MediawikiUser,
    Logging,
    Archive,
)
from wikimetrics.enums import CohortUserRole

mediawiki_project = 'wiki'
second_mediawiki_project = 'wiki2'
tz_note = 'NOTE: if this test is failing by + or - one hour, '\
          'it is *most* likely that Daylight Savings Time is '\
          'in between registration and the revisions you are '\
          'checking.  Wikimetrics should only run on servers '\
          'configured with UTC, and we have decided to ignore'\
          ' these failures rather than complicate the tests.'


def i(date_object):
    """
    helper function to convert dates into integers representing mediawiki timestamps
    """
    return int(format_date(date_object))


def d(integer):
    """
    helper function to parse dates from integers in the mediawiki timestamp format
    """
    return parse_date(str(integer))


class DatabaseTest(unittest.TestCase):
    """
    WARNING: this DESTROYS ALL DATA
    WARNING: making instance methods on test classes is ok, but you
             MUST decorate them as @nottest otherwise they will execute
             as part of test runs
    """
    
    @nottest
    def create_test_cohort(self, **kargs):
        """
        A fast and easy way to create most of the testing data that Metrics need.
        Creates a page, editors with specified registration dates, and a number of
        revisions with specified timestamps for each of those editors.
        NOTE: the engine.execute syntax is used for huge performance gains over ORM
        
        Parameters
            name                    : a unique name to append to everything
            editor_count            : count of editors we want in this cohort
            user_registrations      : the registration date of each editor either as
                                        an integer that applies to all OR
                                        an array of length editor_count
            revisions_per_editor    : count of revisions we want for each editor
            revision_timestamps     : the timestamp of each revision either as
                                        an integer, or datetime that applies to all
                                        revisions OR a two dimensional array indexed by
                                            editor from 0 to editor_count-1
                                            revision from 0 to revisions_per_editor-1
            revision_lengths        : the length of each revision either as
                                        an integer that applies to all revisions OR
                                        a two dimensional array indexed by
                                            editor from 0 to editor_count-1
                                            revision from 0 to revisions_per_editor-1
            page_count              : the number of additional pages to create,
                                        besides the one to which all the revisions
                                        above are targeted (default 0)
            page_timestamps         : the timestamps of page creation as an integer
                                        that applies to all pages or an array
            page_namespaces         : the namespaces to create pages in, as an integer
                                        that applies to all pages or an array
            page_creator_index      : the index into self.editors to assign the first
                                        revision on each page to, as an integer to
                                        assign all pages to the same editor or an
                                        array to specify each one individually
            owner_user_id           : record in the User table that owns this cohort
            page_touched            : required for Page creation, usually default is ok
            user_email_token_expires: required for User creation, usually default is ok
        
        Returns
            Nothing but creates the following, to be accessed in a test:
              self.cohort       : owned by web_test_user, contains self.editors
              self.page         : the page that all the editors edited
              self.editors      : the mediawiki editors from the cohort
              self.revisions    : the revisions added, in a two dimensional array
        """
        self.create_test_data(**kargs)

    @nottest
    def helper_insert_editors(self, **kargs):
        """
        Almost the exact same as `create_test_cohort` EXCEPT:
            * does not create a cohort
            * does not set self.cohort, self.page, self.editors, or self.revisions
            * does not take an `owner_user_id` parameter
        """
        if 'name' not in kargs:
            kargs['name'] = 'test-without-cohort'
        kargs['create_cohort'] = False
        self.create_test_data(**kargs)

    @nottest
    def create_test_data(
        self,
        name='test-specific',
        editor_count=0,
        user_registrations=20130101000000,
        revisions_per_editor=0,
        revision_timestamps=None,
        revision_lengths=None,
        page_count=0,
        page_timestamps=None,
        page_namespaces=None,
        page_creator_index=None,
        owner_user_id=None,
        page_touched=20130102000000,
        user_email_token_expires=20200101000000,
        create_cohort=True,
    ):
        """
        Internal multi-purpose data creator.
        Creates a set of users and, if `name` is specified, wraps them in a cohort.
        """
        if revision_timestamps is None:
            revision_timestamps = []
        if revision_lengths is None:
            revision_lengths = []
        if page_timestamps is None:
            page_timestamps = []
        if page_namespaces is None:
            page_namespaces = []
        if page_creator_index is None:
            page_creator_index = []
        
        if type(revision_timestamps) is datetime:
            revision_timestamps = i(revision_timestamps)
        if type(revision_timestamps) is int:
            revision_timestamps = [
                [revision_timestamps] * revisions_per_editor
            ] * editor_count
        
        if type(revision_lengths) is int:
            revision_lengths = [
                [revision_lengths] * revisions_per_editor
            ] * editor_count
        
        if type(user_registrations) is int:
            user_registrations = [user_registrations] * editor_count
        
        project = mediawiki_project
        if create_cohort:
            cohort = CohortStore(
                name='{0}-cohort'.format(name),
                enabled=True,
                public=False,
                validated=True,
            )
            self.session.add(cohort)
            self.session.commit()
        
        page = Page(page_namespace=0, page_title='{0}-page'.format(name),
                    page_touched=page_touched)
        self.mwSession.add(page)
        self.mwSession.commit()
        
        self.mwSession.bind.engine.execute(
            MediawikiUser.__table__.insert(), [
                {
                    'user_name': 'Editor {0}-{1}'.format(name, e),
                    'user_registration': user_registrations[e],
                    'user_email_token_expires': user_email_token_expires
                }
                for e in range(editor_count)
            ]
        )
        self.mwSession.commit()
        editors = self.mwSession.query(MediawikiUser)\
            .filter(MediawikiUser.user_name.like('Editor {0}-%'.format(name)))\
            .order_by(MediawikiUser.user_id)\
            .all()

        # Create logging table records for each inserted user
        self.mwSession.bind.engine.execute(
            Logging.__table__.insert(), [
                {
                    'log_user': editor.user_id,
                    'log_timestamp': editor.user_registration,
                    'log_title': editor.user_name,
                    'log_type': 'newusers',
                    'log_action': 'create',
                }
                for editor in editors
            ]
        )
        self.mwSession.commit()

        if create_cohort:
            self.session.bind.engine.execute(
                WikiUserStore.__table__.insert(), [
                    {
                        'mediawiki_username'    : editor.user_name,
                        'mediawiki_userid'      : editor.user_id,
                        'project'               : project,
                        'valid'                 : True,
                        'validating_cohort'     : cohort.id,
                    }
                    for editor in editors
                ]
            )
            self.session.commit()
            wiki_users = self.session.query(WikiUserStore)\
                .filter(
                    WikiUserStore.mediawiki_username.like('Editor {0}-%'.format(name)))\
                .all()
            self.session.bind.engine.execute(
                CohortWikiUserStore.__table__.insert(), [
                    {
                        'cohort_id'     : cohort.id,
                        'wiki_user_id'  : wiki_user.id,
                    }
                    for wiki_user in wiki_users
                ]
            )
            self.session.commit()
        
        self.mwSession.bind.engine.execute(
            Revision.__table__.insert(), [
                {
                    'rev_page'      : page.page_id,
                    'rev_user'      : editors[e].user_id,
                    'rev_comment'   : 'revision {0}, editor {1}'.format(r, e),
                    'rev_timestamp' : revision_timestamps[e][r] or UNICODE_NULL * 14,
                    'rev_len'       : revision_lengths[e][r],
                    # rev_parent_id will be set below, following chronology
                }
                for e, r in product(range(editor_count), range(revisions_per_editor))
            ]
        )
        self.mwSession.commit()
        revisions = self.mwSession.query(Revision)\
            .filter(Revision.rev_page == page.page_id)\
            .order_by(Revision.rev_id)\
            .all()
        
        # add rev_parent_id chain in chronological order
        real_revisions = filter(lambda r: r.rev_timestamp, revisions)
        ordered_revisions = sorted(real_revisions, key=lambda r: r.rev_timestamp)
        for idx, revision in enumerate(ordered_revisions):
            if idx == 0:
                revision.rev_parent_id = 0
            else:
                revision.rev_parent_id = ordered_revisions[idx - 1].rev_id
        
        self.mwSession.commit()
        
        if create_cohort:
            # establish ownership for this cohort
            if not owner_user_id:
                owner = UserStore(username='test cohort owner', email='test@test.com')
                self.session.add(owner)
                self.session.commit()
                owner_user_id = owner.id

            self.session.add(CohortUserStore(
                user_id=owner_user_id,
                cohort_id=cohort.id,
                role=CohortUserRole.OWNER,
            ))
            self.session.commit()
        
        if page_count > 0:
            # create any additional pages
            if type(page_timestamps) is int:
                page_timestamps = [page_timestamps] * page_count
            if type(page_namespaces) is int:
                page_namespaces = [page_namespaces] * page_count
            if type(page_creator_index) is int:
                page_creator_index = [page_creator_index] * page_count
            
            self.mwSession.bind.engine.execute(
                Page.__table__.insert(), [
                    {
                        'page_namespace'    : page_namespaces[p],
                        'page_title'        : '{0}-additional-page-{1}'.format(name, p),
                        'page_touched'      : page_touched
                    }
                    for p in range(page_count)
                ]
            )
            self.mwSession.commit()
            pages = self.mwSession.query(Page)\
                .filter(Page.page_title.like('{0}-additional-page-%'.format(name)))\
                .order_by(Page.page_id)\
                .all()
            
            self.mwSession.bind.engine.execute(
                Revision.__table__.insert(), [
                    {
                        'rev_page'      : pages[p].page_id,
                        'rev_user'      : editors[page_creator_index[p]].user_id,
                        'rev_comment'   : 'page {0} created'.format(p),
                        'rev_timestamp' : page_timestamps[p],
                        'rev_len'       : 10,
                        'rev_parent_id' : 0,
                    }
                    for p in range(page_count)
                ]
            )
            self.mwSession.commit()

        if create_cohort:
            self.project = project

            # TODO this is a storage object, should be changed
            # for metrics tests into a logic object, not a storage object
            self.cohort = cohort
            self.page = page
            self.editors = editors
            self.editor_ids = [e.user_id for e in editors]
            self.revisions = revisions
            self.owner_user_id = owner_user_id
    
    @nottest
    def editor(self, index):
        """Gets the proper key to look up a member of a create_test_cohort result"""
        return str(WikiUserKey(
            self.editors[index].user_id,
            mediawiki_project,
            self.cohort.id,
        ))
    
    @nottest
    def helper_reset_validation(self):
        wikiusers = self.session.query(WikiUserStore) \
            .join(CohortWikiUserStore) \
            .filter(CohortWikiUserStore.cohort_id == self.cohort.id) \
            .all()
        for wu in wikiusers:
            wu.validating_cohort = self.cohort.id
            wu.valid = None
        self.cohort.validated = False
        self.cohort.validate_as_user_ids = True
        self.session.commit()
    
    @nottest
    def helper_remove_authorization(self):
        cu = self.session.query(CohortUserStore) \
            .filter(CohortUserStore.cohort_id == self.cohort.id) \
            .one()
        cu.role = 'UNAUTHORIZED'
        self.session.commit()
    
    @nottest
    def common_cohort_1(self, cohort=True):
        if cohort:
            method = self.create_test_cohort
        else:
            method = self.helper_insert_editors

        method(
            editor_count=4,
            revisions_per_editor=4,
            revision_timestamps=[
                [20121231230000, 20130101003000, 20130101010000, 20140101010000],
                [20130101120000, 20130102000000, 20130102120000, 20130103120000],
                [20130101000000, 20130108000000, 20130116000000, 20130216000000],
                [20130101000000, 20130201000000, 20140101000000, 20140102000000],
            ],
            revision_lengths=10
        )
    
    @nottest
    def common_cohort_2(self, cohort=True):
        if cohort:
            method = self.create_test_cohort
        else:
            method = self.helper_insert_editors

        method(
            editor_count=3,
            revisions_per_editor=3,
            revision_timestamps=[
                [20121231230000, 20130101003000, 20130101010000],
                [20130101120000, 20130102000000, 20130102120000],
                [None, None, None],
            ],
            revision_lengths=[
                [100, 0, 10],
                [100, 140, 136],
                [None, None, None],
            ],
        )
    
    @nottest
    def common_cohort_3(self, cohort=True):
        if cohort:
            method = self.create_test_cohort
        else:
            method = self.helper_insert_editors

        method(
            editor_count=4,
            revisions_per_editor=4,
            # in order, all in 2013:
            # 1/1, 1/5, 1/9, 1/13, 2/2, 2/6, 2/10, 2/14, 3/3, 3/7, 3/15, 4/4, 4/12, 4/16
            revision_timestamps=[
                [20130101010000, 20130202000000, 20130303000000, 20130404000000],
                [20130105000000, 20130206000000, 20130307000000, 20130408000000],
                [20130109000000, 20130210000000, 20130311000000, 20130412000000],
                [20130113000000, 20130214000000, 20130315000000, 20130416000000],
            ],
            # in order:
            # 100,1100,1200,1300,0,200,400,600,800,700,600,500,590,550,600,650
            revision_lengths=[
                [100, 0, 800, 590],
                [1100, 200, 700, 550],
                [1200, 400, 600, 600],
                [1300, 600, 500, 650],
            ],
        )
    
    @nottest
    def common_cohort_4(self, cohort=True):
        if cohort:
            method = self.create_test_cohort
        else:
            method = self.helper_insert_editors

        method(
            editor_count=2,
            revisions_per_editor=1,
            revision_timestamps=20130416000000,
            revision_lengths=10,
            page_count=4,
            page_timestamps=[
                20130619000001, 20130620000000, 20130821000000, 20130701000000
            ],
            page_namespaces=[301, 302, 303, 301],
            page_creator_index=[0, 0, 0, 1],
        )
    
    @nottest
    def common_cohort_5(self, cohort=True):
        if cohort:
            method = self.create_test_cohort
        else:
            method = self.helper_insert_editors

        method(
            editor_count=4,
            revisions_per_editor=4,
            revision_timestamps=[
                [20130101000001, 20130201010000, 20130201010100, 20130301020100],
                [20130101000001, 20130201010000, 20130201010100, 20130301020100],
                [20110101000001, 20110201010000, 20110201010100, 20110301020100],
                [20110101000001, 20110201010000, 20110201010100, 20110301020100]
            ],
            revision_lengths=10,
        )

    @nottest
    def create_non_editors(self, user_tuples, name='some-identifier'):
        """
        Creates plain users that haven't edited anything.
        You should pass a unique prefix parameter if called 2+ times before tearDown.

        Parameters
            user_tuples : tuples in the form:
                          (<user_registration>, <log_type>, <log_action>)
        """
        by_name = {
            'non-editor-user-{0}-{1}'.format(name, i): u
            for i, u in enumerate(user_tuples)
        }
        self.mwSession.bind.engine.execute(
            MediawikiUser.__table__.insert(), [
                {
                    'user_name': key,
                    'user_registration': user[0],
                    'user_email_token_expires': 20200101000000,
                }
                for key, user in by_name.items()
            ]
        )
        self.mwSession.commit()
        self.non_editors = users = self.mwSession.query(MediawikiUser)\
            .filter(MediawikiUser.user_name.like('non-editor-user-{0}-%'.format(name)))\
            .order_by(MediawikiUser.user_id)\
            .all()

        self.mwSession.bind.engine.execute(
            Logging.__table__.insert(), [
                {
                    'log_user': user.user_id,
                    'log_title': user.user_name,
                    'log_timestamp': user.user_registration,
                    'log_type': by_name[user.user_name][1],
                    'log_action': by_name[user.user_name][2],
                }
                for user in users
            ]
        )
        self.mwSession.commit()

    @nottest
    def create_wiki_cohort(self, project=mediawiki_project):
        """
        Creates a wiki cohort (spans a whole project)
        and an owner for the cohort
        """
        # cohort data
        basic_wiki_cohort = CohortStore(name='{0}-wiki-cohort'.format(project),
                                        enabled=True,
                                        public=False,
                                        default_project=project,
                                        class_name='WikiCohort'
                                        )
        self.session.add(basic_wiki_cohort)
        self.session.commit()
        self.basic_wiki_cohort = basic_wiki_cohort
        
        owner = UserStore(username='test cohort owner', email='test@test.com')
        self.session.add(owner)
        self.session.commit()
        self.owner_user_id = owner.id
        
        cohort_user = CohortUserStore(
            user_id=self.owner_user_id,
            cohort_id=basic_wiki_cohort.id,
            role=CohortUserRole.OWNER
        )
        self.session.add(cohort_user)
        self.session.commit()
        self.basic_wiki_cohort_owner = cohort_user

    def archive_revisions(self):
        """
        Archive all the revisions in the revision table
        NOTE: only populates ar_timestamp, and ar_user
        NOTE: leaves ar_rev_id NULL because that's valid and a good edge case
        NOTE: creates duplicates with NULL ar_rev_id
        """
        query = self.mwSession.query(Revision)
        revisions = query.all()
        self.mwSession.execute(
            Archive.__table__.insert(), [
                {
                    'ar_rev_id': None,
                    'ar_timestamp': r.rev_timestamp,
                    'ar_user': r.rev_user
                }
                for r in revisions
            ]
        )

        query.delete()
        self.mwSession.commit()

    def setUp(self):
        #****************************************************************
        # set up and clean database (Warning: this DESTROYS ALL DATA)
        #****************************************************************
        self.session = db.get_session()
        engine = db.get_mw_engine(mediawiki_project)
        db.MediawikiBase.metadata.create_all(engine, checkfirst=True)
        engine2 = db.get_mw_engine(second_mediawiki_project)
        db.MediawikiBase.metadata.create_all(engine2, checkfirst=True)
        # mediawiki_project is a global defined on this file
        self.mwSession = db.get_mw_session(mediawiki_project)
        self.mwSession2 = db.get_mw_session(second_mediawiki_project)
        DatabaseTest.tearDown(self)
    
    def tearDown(self):

        # delete records
        self.mwSession.query(Logging).delete()
        self.mwSession.query(Revision).delete()
        self.mwSession.query(Archive).delete()
        self.mwSession.query(MediawikiUser).delete()
        self.mwSession.query(Page).delete()
        self.mwSession.commit()
        self.mwSession.close()
        
        self.mwSession2.query(Logging).delete()
        self.mwSession2.query(Revision).delete()
        self.mwSession2.query(Archive).delete()
        self.mwSession2.query(MediawikiUser).delete()
        self.mwSession2.query(Page).delete()
        self.mwSession2.commit()
        self.mwSession2.close()
        
        self.session.query(CohortTagStore).delete()
        self.session.query(TagStore).delete()
        self.session.query(CohortWikiUserStore).delete()
        self.session.query(CohortUserStore).delete()
        self.session.query(WikiUserStore).delete()
        self.session.query(CohortStore).delete()
        self.session.query(UserStore).delete()
        self.session.query(ReportStore).delete()
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
        self.common_cohort_5()
        self.client = app.test_client()
        
        # TODO change all tests, tests than inherit from
        # WebTest expect self.app = app.test_client()
        # this is confusing, app and test_client are two different things
        # app should refer to the global object
        # have changed only test_reports.py to use client
        self.app = self.client
        
        self.logger = Mock(spec=RootLogger)
    
    def tearDown(self):
        DatabaseTest.tearDown(self)


class WebTest(WebTestAnonymous):
    """
    Creates a test flask client from the normally configured app.
    Makes sure that a user is authenticated as far as Flask-Login is concerned,
    so that any private routes are still served for testing purposes.
    NOTE: to simulate ajax requests, do this
        self.app.get('/', headers=[('X-Requested-With', 'XMLHttpRequest')])
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
