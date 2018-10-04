import unittest
import mock
import os
from nose.tools import assert_equal, raises, assert_true, assert_false, nottest
from wikimetrics.configurables import app, get_absolute_path
from tests.fixtures import WebTest, QueueDatabaseTest, DatabaseTest, mediawiki_project
from wikimetrics.forms import CohortUpload
from wikimetrics.models import (
    CohortStore, WikiUserStore, UserStore,
    MediawikiUser, ValidateCohort, normalize_project,
)
from wikimetrics.utils import parse_username


def mock_normalize_project_pass(project):
    # does not check wrong project names
    # this will force database connection errors
    return project


def mock_normalize_project_fixed(project):
    # always returns the same value
    return 'wiki'


class MockCohort(object):
    pass


class ValidateCohortEncodingTest(DatabaseTest):

    def setUp(self):
        DatabaseTest.setUp(self)
        self.test_report_path = os.path.join(get_absolute_path(), os.pardir, 'tests')

    def tearDown(self):
        pass

    def test_validate_arabic_cohort(self):
        '''
        Cohort with arabic names should validate

        If cohorts uploads are failing you could substitute
        the file on this test by your file to test uploads.

        Note this test does not test the parsing of the
        cohort file done at the controller layer.
        '''
        self.validate_cohort('testing-cohort-arabic.txt')

    def test_validate_cyrilic_cohort(self):
        '''
        Cohort with cyrilic names should validate

        Note this test does not test the parsing of the
        cohort file done at the controller layer.
        '''
        self.validate_cohort('testing-cohort-cyrilic.txt')

    @nottest
    def validate_cohort(self, filename):
        '''
        Given a cohort file with usernames all users but one should validate.
        It will mingle the name of the 1st user.

        Parameters:
            filename : Name of a file that contains a cohort with user names
                       test will search for file in tests/static/public folder
        '''

        names = self.create_users_from_file(filename)

        # establish ownership for this cohort otherwise things do not work
        owner_user = UserStore(username='test cohort owner', email='test@test.com')
        self.session.add(owner_user)
        self.session.commit()

        # creating here kind of like a cohortupload mock
        # flask forms do not lend themselves to easy mocking
        cohort_upload = MockCohort()
        cohort_upload.name = MockCohort()
        cohort_upload.name.data = 'testing-cohort'
        cohort_upload.description = MockCohort()
        cohort_upload.description.data = 'testing-cohort'
        cohort_upload.project = MockCohort()
        cohort_upload.project.data = mediawiki_project
        cohort_upload.validate_as_user_ids = MockCohort()
        cohort_upload.validate_as_user_ids.data = False
        cohort_upload.records = []

        # mingle the name of the first user user
        not_valid_editor_name = 'Mr Not Valid'
        names[0] = not_valid_editor_name

        for name in names:
            cohort_upload.records.append({
                'raw_id_or_name'  : name,
                'project'   : mediawiki_project,
            })

        # TODO clear session situation?
        # all operations need to happen on the scope of the same session
        # but this session passed in is going to be closed
        vc = ValidateCohort.from_upload(cohort_upload, owner_user.id, self.session)

        cohort = self.session.query(CohortStore).first()
        self.session.commit()
        vc.validate_records(self.session, cohort)

        # now we need to assert that all users but the first one validate
        assert_equal(len(
            self.session.query(WikiUserStore)
                .filter(WikiUserStore.validating_cohort == cohort.id)
                .filter(WikiUserStore.valid)
                .all()
        ), len(names) - 1)

        # retrieve the user that should not be valid, make sure it is not indeed
        wiki_user = self.session.query(WikiUserStore)\
            .filter(WikiUserStore.validating_cohort == cohort.id)\
            .filter(WikiUserStore.raw_id_or_name == not_valid_editor_name).one()

        assert_false(wiki_user.valid)

    @nottest
    def create_users_from_file(self, filename):
        """
        Adds a bunch of users to mediawiki user table from a file
        with usernames.

        In order to test encoding make sure the bindings of the testing and production
        databases match, we try to replicate as accurate as possible the structure
        of mediawiki db in our testing db but that is ongoing work that needs to be
        maintaned.

        Parameters:
            filename : Name of a file that contains a cohort with user names
                       test will search for file in tests/static/public folder
        Return:
            names: Array with the names of the users created as they appear on the file
                   but capitalized to mediawiki convention
        """

        # open the cohort file
        test_cohort_file = os.sep.join((self.test_report_path, 'static',
                                        'public', filename))
        f = open(test_cohort_file, 'r')
        names = []

        # format names according to our convention
        for line in f:
            name = parse_username(line.strip())
            names.append(name)

        self.mwSession.bind.engine.execute(
            MediawikiUser.__table__.insert(), [
                {
                    'user_name': '{0}'.format(n),
                    'user_registration': 20130101000000,
                    'user_email_token_expires': 20200101000000
                }
                for n in names
            ]
        )
        self.mwSession.commit()

        return names


class ValidateCohortTest(WebTest):

    def test_normalize_project_shorthand(self):
        normal = normalize_project('en')
        assert_equal(normal, 'enwiki')

    def test_normalize_project_uppercase(self):
        normal = normalize_project(mediawiki_project.upper())
        assert_equal(normal, mediawiki_project)

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
            self.session.query(WikiUserStore)
                .filter(WikiUserStore.validating_cohort == self.cohort.id)
                .filter(WikiUserStore.valid)
                .all()
        ), 4)

    def test_validate_cohorts_with_invalid_wikiusers(self):
        self.helper_reset_validation()
        self.cohort.validate_as_user_ids = False
        wikiusers = self.session.query(WikiUserStore).all()
        wikiusers[0].project = 'blah'
        wikiusers[1].raw_id_or_name = 'blah'
        self.session.commit()
        v = ValidateCohort(self.cohort)
        v.validate_records(self.session, self.cohort)

        assert_equal(self.cohort.validated, True)
        assert_equal(len(
            self.session.query(WikiUserStore)
                .filter(WikiUserStore.validating_cohort == self.cohort.id)
                .filter(WikiUserStore.valid)
                .all()
        ), 2)
        assert_equal(len(
            self.session.query(WikiUserStore)
                .filter(WikiUserStore.validating_cohort == self.cohort.id)
                .filter(WikiUserStore.valid.in_([False]))
                .all()
        ), 2)

    @mock.patch('wikimetrics.models.validate_cohort.normalize_project',
                side_effect=mock_normalize_project_fixed)
    def test_validate_cohorts_with_project_variations(self, mock):
        self.helper_reset_validation()
        self.cohort.validate_as_user_ids = False

        wikiusers = self.session.query(WikiUserStore).all()
        username = 'Same Name'
        wikiusers[0].raw_id_or_name = username
        wikiusers[1].raw_id_or_name = username
        # set different project versions of the same project
        # they will be normalized to 'wiki' by the normalize_project mock
        wikiusers[0].project = 'en'
        wikiusers[1].project = 'enwiki'
        # add also the correspondent mediawiki user
        self.mwSession.add(MediawikiUser(user_name=username))
        self.mwSession.commit()

        v = ValidateCohort(self.cohort)
        v.validate_records(self.session, self.cohort)

        assert_equal(self.cohort.validated, True)
        assert_equal(len(
            self.session.query(WikiUserStore)
                .filter(WikiUserStore.validating_cohort == self.cohort.id)
                .filter(WikiUserStore.valid)
                .all()
        ), 3)
        assert_equal(len(
            self.session.query(WikiUserStore)
                .filter(WikiUserStore.validating_cohort == self.cohort.id)
                .filter(WikiUserStore.valid.in_([False]))
                .all()
        ), 0)

    @mock.patch('wikimetrics.models.validate_cohort.normalize_project',
                side_effect=mock_normalize_project_pass)
    def test_validate_cohorts_when_invalid_project_causes_exception(self, mock):
        '''
        Mocks normalize_project to force an exception when accessing
        an unexisting project database. This exception should not be
        forwarded.
        '''
        self.helper_reset_validation()
        self.cohort.validate_as_user_ids = False
        wikiusers = self.session.query(WikiUserStore).all()
        wikiusers[0].project = 'blah'
        v = ValidateCohort(self.cohort)
        try:
            v.validate_records(self.session, self.cohort)
        except Exception:
            assert_true(False, 'validate_records should not raise an exception')
        else:
            assert_equal(self.cohort.validated, True)
            assert_equal(len(
                self.session.query(WikiUserStore)
                    .filter(WikiUserStore.validating_cohort == self.cohort.id)
                    .filter(WikiUserStore.valid)
                    .all()
            ), 3)
            records = (self.session.query(WikiUserStore)
                       .filter(WikiUserStore.validating_cohort == self.cohort.id)
                       .filter(WikiUserStore.valid.in_([False]))
                       .all())
            assert_equal(len(records), 1)
            assert_equal(records[0].reason_invalid, 'invalid project')


class ValidateCohortQueueTest(QueueDatabaseTest):

    def setUp(self):
        QueueDatabaseTest.setUp(self)
        self.mwSession.add(MediawikiUser(user_name='Editor test-specific-0'))
        self.mwSession.add(MediawikiUser(user_name='Editor test-specific-1'))
        self.mwSession.commit()

        owner_user = UserStore()
        self.session.add(owner_user)
        self.session.commit()
        self.owner_user_id = owner_user.id

    def test_small_cohort(self):
        cohort_upload = CohortUpload()
        cohort_upload.name.data = 'small_cohort'
        cohort_upload.project.data = mediawiki_project
        cohort_upload.records = [
            # two existing users
            {'raw_id_or_name': 'Editor test-specific-0', 'project': mediawiki_project},
            {'raw_id_or_name': 'Editor test-specific-1', 'project': mediawiki_project},
            # one invalid username
            {'raw_id_or_name': 'Nonexisting', 'project': mediawiki_project},
            # one user with invalid project
            {'raw_id_or_name': 'Nonexisting2', 'project': 'Nonexisting'},
        ]

        v = ValidateCohort.from_upload(cohort_upload, self.owner_user_id)
        v.task.delay(v).get()
        self.session.commit()

        assert_equal(self.session.query(WikiUserStore).filter(
            WikiUserStore.raw_id_or_name == 'Editor test-specific-0').one().valid,
            True
        )
        assert_equal(self.session.query(WikiUserStore).filter(
            WikiUserStore.raw_id_or_name == 'Editor test-specific-1').one().valid,
            True
        )
        assert_equal(self.session.query(WikiUserStore).filter(
            WikiUserStore.raw_id_or_name == 'Nonexisting').one().valid, False)
        assert_equal(self.session.query(WikiUserStore).filter(
            WikiUserStore.raw_id_or_name == 'Nonexisting2').one().valid, False)

    def test_from_upload_exception(self):
        cohort_upload = CohortUpload()
        cohort_upload.name.data = 'small_cohort'
        cohort_upload.project.data = 'wiki'
        cohort_upload.records = [{'fake': 'dict'}]

        v = ValidateCohort.from_upload(cohort_upload, self.owner_user_id)
        assert_equal(v, None)


class BasicTests(unittest.TestCase):

    def test_repr(self):
        cohort = CohortStore(id=1)
        v = ValidateCohort(cohort)
        assert_equal(str(v), '<ValidateCohort("1")>')
