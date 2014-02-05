import unittest
import sys
from itertools import product
from datetime import datetime
from wikimetrics.utils import (
    parse_date, format_date, parse_pretty_date, format_pretty_date, UNICODE_NULL
)
from nose.tools import nottest

__all__ = [
    'DatabaseTest',
    'QueueTest',
    'QueueDatabaseTest',
    'WebTest',
    'i',
    'd',
    'tz_note',
    'mediawiki_project'
]

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

# this should not be used as the db name
# as in testing project and db name are different
mediawiki_project = 'wiki'


class DatabaseTest(unittest.TestCase):
    """
    WARNING: this DESTROYS ALL DATA
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
        user_email_token_expires=20200101000000
    ):
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
                                        an integer that applies to all revisions OR
                                        a two dimensional array indexed by
                                            editor from 0 to editor_count-1
                                            revision from 0 to revisions_per_editor-1
            revision_timestamps     : the length of each revision either as
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

        self.project = mediawiki_project

        self.cohort = Cohort(
            name='{0}-cohort'.format(name),
            enabled=True,
            public=False,
            validated=True,
        )
        self.session.add(self.cohort)
        self.session.commit()

        self.page = Page(page_namespace=0, page_title='{0}-page'.format(name),
                         page_touched=page_touched)
        self.mwSession.add(self.page)
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
        self.editors = self.mwSession.query(MediawikiUser)\
            .filter(MediawikiUser.user_name.like('Editor {0}-%'.format(name)))\
            .order_by(MediawikiUser.user_id)\
            .all()
        self.session.bind.engine.execute(
            WikiUser.__table__.insert(), [
                {
                    'mediawiki_username'    : editor.user_name,
                    'mediawiki_userid'      : editor.user_id,
                    'project'               : self.project,
                    'valid'                 : True,
                    'validating_cohort'     : self.cohort.id,
                }
                for editor in self.editors
            ]
        )
        self.session.commit()
        wiki_users = self.session.query(WikiUser)\
            .filter(WikiUser.mediawiki_username.like('Editor {0}-%'.format(name)))\
            .all()
        self.session.bind.engine.execute(
            CohortWikiUser.__table__.insert(), [
                {
                    'cohort_id'     : self.cohort.id,
                    'wiki_user_id'  : wiki_user.id,
                }
                for wiki_user in wiki_users
            ]
        )
        self.session.commit()

        self.mwSession.bind.engine.execute(
            Revision.__table__.insert(), [
                {
                    'rev_page'      : self.page.page_id,
                    'rev_user'      : self.editors[e].user_id,
                    'rev_comment'   : 'revision {0}, editor {1}'.format(r, e),
                    'rev_timestamp' : revision_timestamps[e][r] or UNICODE_NULL * 14,
                    'rev_len'       : revision_lengths[e][r],
                    # rev_parent_id will be set below, following chronology
                }
                for e, r in product(range(editor_count), range(revisions_per_editor))
            ]
        )
        self.mwSession.commit()
        self.revisions = self.mwSession.query(Revision)\
            .filter(Revision.rev_page == self.page.page_id)\
            .order_by(Revision.rev_id)\
            .all()

        # add rev_parent_id chain in chronological order
        real_revisions = filter(lambda r: r.rev_timestamp, self.revisions)
        ordered_revisions = sorted(real_revisions, key=lambda r: r.rev_timestamp)
        for i, revision in enumerate(ordered_revisions):
            if i == 0:
                revision.rev_parent_id = 0
            else:
                revision.rev_parent_id = ordered_revisions[i - 1].rev_id

        self.mwSession.commit()

        # establish ownership for this cohort
        if not owner_user_id:
            owner_user = User(username='test cohort owner', email='test@test.com')
            self.session.add(owner_user)
            self.session.commit()
            self.owner_user_id = owner_user.id

        self.session.add(CohortUser(
            user_id=self.owner_user_id,
            cohort_id=self.cohort.id,
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
                        'rev_user'      : self.editors[page_creator_index[p]].user_id,
                        'rev_comment'   : 'page {0} created'.format(p),
                        'rev_timestamp' : page_timestamps[p],
                        'rev_len'       : 10,
                        'rev_parent_id' : 0,
                    }
                    for p in range(page_count)
                ]
            )
            self.mwSession.commit()

    @nottest
    def helper_reset_validation(self):
        wikiusers = self.session.query(WikiUser) \
            .join(CohortWikiUser) \
            .filter(CohortWikiUser.cohort_id == self.cohort.id) \
            .all()
        for wu in wikiusers:
            wu.validating_cohort = self.cohort.id
            wu.valid = None
        self.cohort.validated = False
        self.cohort.validate_as_user_ids = True
        self.session.commit()

    @nottest
    def helper_remove_authorization(self):
        cu = self.session.query(CohortUser) \
            .filter(CohortUser.cohort_id == self.cohort.id) \
            .one()
        cu.role = 'UNAUTHORIZED'
        self.session.commit()

    @nottest
    def common_cohort_1(self):
        self.create_test_cohort(
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
    def common_cohort_2(self):
        self.create_test_cohort(
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
    def common_cohort_3(self):
        self.create_test_cohort(
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
    def common_cohort_4(self):
        self.create_test_cohort(
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
    def common_cohort_5(self):
        self.create_test_cohort(
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

    def setUp(self):
        #****************************************************************
        # set up and clean database (Warning: this DESTROYS ALL DATA)
        #****************************************************************
        self.session = db.get_session()
        engine = db.get_mw_engine(mediawiki_project)
        db.MediawikiBase.metadata.create_all(engine, checkfirst=True)
        # mediawiki_project is a global defined on this file
        self.mwSession = db.get_mw_session(mediawiki_project)
        DatabaseTest.tearDown(self)

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
        self.common_cohort_5()
        self.app = app.test_client()

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
