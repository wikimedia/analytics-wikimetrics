import json
import time
from contextlib import contextmanager
from flask import appcontext_pushed, g
from StringIO import StringIO
from nose.tools import assert_equal, assert_not_equal, assert_true

from wikimetrics.api import CohortService
from wikimetrics.configurables import app
from tests.fixtures import WebTest
from wikimetrics.models import (
    CohortStore, CohortUserStore, CohortWikiUserStore, WikiUserStore, UserStore,
    ValidateCohort, CohortTagStore, TagStore
)
from wikimetrics.enums import CohortUserRole


@contextmanager
def cohort_service_set(app, cohort_service):
    def handler(sender, **kwargs):
        g.cohort_service = cohort_service
    with appcontext_pushed.connected_to(handler, app):
        yield


class CohortsControllerTest(WebTest):
    def setUp(self):
        WebTest.setUp(self)
        self.cohort_service = CohortService()

    def test_index(self):
        response = self.app.get('/cohorts/', follow_redirects=True)
        assert_equal(response.status_code, 200)

    def test_list(self):
        response = self.app.get('/cohorts/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(parsed['cohorts'][0]['name'], self.cohort.name)

    def test_list_includes_only_validated(self):
        # There is already one cohort, add one more validated and one not validated
        cohorts = [
            CohortStore(name='c1', enabled=True, validated=False),
            CohortStore(name='c2', enabled=True, validated=True),
            CohortStore(name='c3', enabled=True, validated=True)
        ]
        self.session.add_all(cohorts)
        self.session.commit()
        owners = [
            CohortUserStore(
                cohort_id=c.id,
                user_id=self.owner_user_id,
                role=CohortUserRole.OWNER
            )
            for c in cohorts
        ]
        self.session.add_all(owners)
        c1_user = WikiUserStore(valid=True)
        c3_user = WikiUserStore(valid=True)
        self.session.add_all([c1_user, c3_user])
        self.session.commit()

        self.session.add_all([
            CohortWikiUserStore(wiki_user_id=c1_user.id, cohort_id=cohorts[0].id),
            CohortWikiUserStore(wiki_user_id=c3_user.id, cohort_id=cohorts[2].id)
        ])
        self.session.commit()

        response = self.app.get('/cohorts/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(len(parsed['cohorts']), 2)
        assert_true(self.cohort.name in [c['name'] for c in parsed['cohorts']])
        assert_true('c3' in [c['name'] for c in parsed['cohorts']])

    def test_detail(self):
        with cohort_service_set(app, self.cohort_service):
            response = self.app.get('/cohorts/detail/{0}'.format(self.cohort.id))
        parsed = json.loads(response.data)
        assert_equal(response.status_code, 200)
        assert_equal(parsed['public'], False)

    def test_detail_by_name(self):
        with cohort_service_set(app, self.cohort_service):
            response = self.app.get('/cohorts/detail/{0}'.format(self.cohort.name))
        parsed = json.loads(response.data)
        assert_equal(response.status_code, 200)
        # this cohort did not go through async validation
        assert_equal(parsed['validation']['validation_status'], 'UNKNOWN')
        assert_equal(parsed['validation']['validated_count'], 4)
        assert_equal(parsed['validation']['total_count'], 4)

    def test_detail_by_name_after_validate(self):
        self.helper_reset_validation()

        # Set a fake validation_queue_key as we are running in sync mode
        self.cohort.validation_queue_key = '33'
        self.session.add(self.cohort)
        self.session.commit()

        # executed validation synchronously
        vc = ValidateCohort(self.cohort)
        vc.validate_records(self.session, self.cohort)
        with cohort_service_set(app, self.cohort_service):
            response = self.app.get('/cohorts/detail/{0}'.format(self.cohort.name))
            parsed = json.loads(response.data)

        # note than it does not make sense to assert validation status
        # as that is retrieved directly from celery and celery was not used in this test
        assert_equal(parsed['validation']['validated_count'], 4)
        assert_equal(parsed['validation']['total_count'], 4)

    def test_detail_allowed_if_invalid(self):
        self.helper_reset_validation()
        with cohort_service_set(app, self.cohort_service):
            response = self.app.get('/cohorts/detail/{0}'.format(self.cohort.name))
        parsed = json.loads(response.data)
        assert_equal(parsed['validation']['validation_status'], 'UNKNOWN')
        assert_equal(parsed['validation']['validated_count'], 0)
        assert_equal(parsed['validation']['total_count'], 0)

    def test_full_detail(self):
        with cohort_service_set(app, self.cohort_service):
            response = self.app.get('/cohorts/detail/{0}?full_detail=true'.format(
                self.cohort.id
            ))
        assert_equal(response.status_code, 200)

    def test_detail_not_allowed(self):
        self.helper_remove_authorization()
        with cohort_service_set(app, self.cohort_service):
            response = self.app.get('/cohorts/detail/{0}'.format(self.cohort.id))
        assert_equal(response.status_code, 401)
        assert_equal(response.data, 'You are not allowed to access this Cohort')

    def test_detail_not_found(self):
        with cohort_service_set(app, self.cohort_service):
            response = self.app.get('/cohorts/detail/{0}'.format(-999))
        assert_equal(response.status_code, 404)
        assert_equal(response.data, 'Could not find this Cohort')

    def test_validate_cohort_name_allowed(self):
        response = self.app.get('/cohorts/validate/name?name=sleijslij')

        assert_equal(response.status_code, 200)
        assert_equal(json.loads(response.data), True)

    def test_validate_cohort_name_not_allowed(self):
        response = self.app.get('/cohorts/validate/name?name={0}'.format(
            self.cohort.name)
        )

        assert_equal(response.status_code, 200)
        assert_equal(json.loads(response.data), False)

    def test_validate_cohort_project_allowed(self):
        response = self.app.get('/cohorts/validate/project?project=wiki')

        assert_equal(response.status_code, 200)
        assert_equal(json.loads(response.data), True)

    def test_validate_nonexistent_cohort(self):
        with cohort_service_set(app, self.cohort_service):
            response = self.app.post('/cohorts/validate/0')

        assert_true(response.data.find('isError') >= 0)
        assert_true(response.data.find('This cohort does not exist') >= 0)

    def test_validate_unauthorized_cohort(self):
        self.helper_remove_authorization()
        with cohort_service_set(app, self.cohort_service):
            response = self.app.post('/cohorts/validate/{0}'.format(self.cohort.id))

        assert_true(response.data.find('isError') >= 0)
        assert_true(response.data.find('You are not allowed to access this cohort') >= 0)

    def test_validate_cohort_again_after_upload(self):
        self.helper_reset_validation()
        with cohort_service_set(app, self.cohort_service):
            response = self.app.post('/cohorts/validate/{0}'.format(self.cohort.id))

        assert_true(response.data.find('message') >= 0)
        assert_true(
            response.data.find('Validating cohort') >= 0
        )

    def test_delete_cohort_owner_no_viewer(self):
        response = self.app.post('/cohorts/delete/{0}'.format(self.cohort.id))

        assert_equal(response.status_code, 200)
        assert_true(response.data.find('isRedirect') >= 0)
        assert_true(response.data.find('/cohorts/') >= 0)
        cohort_id = self.cohort.id
        self.session.commit()

        # Check that all relevant rows are deleted
        cwu = self.session.query(CohortWikiUserStore) \
            .filter(CohortWikiUserStore.cohort_id == cohort_id) \
            .first()
        assert_equal(cwu, None)
        cu = self.session.query(CohortUserStore) \
            .filter(CohortUserStore.cohort_id == cohort_id) \
            .filter(CohortUserStore.user_id == self.owner_user_id) \
            .first()
        assert_equal(cu, None)
        wu = self.session.query(WikiUserStore) \
            .filter(WikiUserStore.validating_cohort == cohort_id) \
            .first()
        assert_equal(wu, None)
        c = self.session.query(CohortStore).get(cohort_id)
        assert_equal(c, None)

    def test_delete_cohort_owner_has_viewer(self):
        viewer_user = UserStore()
        self.session.add(viewer_user)
        self.session.commit()

        viewer_cohort_user = CohortUserStore(
            user_id=viewer_user.id,
            cohort_id=self.cohort.id,
            role=CohortUserRole.VIEWER
        )
        self.session.add(viewer_cohort_user)
        self.session.commit()
        response = self.app.post('/cohorts/delete/{0}'.format(self.cohort.id))

        assert_equal(response.status_code, 200)
        assert_true(response.data.find('isRedirect') >= 0)
        assert_true(response.data.find('/cohorts/') >= 0)
        cohort_id = self.cohort.id
        self.session.commit()

        # Check that all relevant rows are deleted
        cwu = self.session.query(CohortWikiUserStore) \
            .filter(CohortWikiUserStore.cohort_id == cohort_id) \
            .first()
        assert_equal(cwu, None)
        cu = self.session.query(CohortUserStore) \
            .filter(CohortUserStore.cohort_id == cohort_id) \
            .first()
        assert_equal(cu, None)
        wu = self.session.query(WikiUserStore) \
            .filter(WikiUserStore.validating_cohort == cohort_id) \
            .first()
        assert_equal(wu, None)
        c = self.session.query(CohortStore).get(cohort_id)
        assert_equal(c, None)

    def test_delete_cohort_as_viewer(self):
        # Changing the owner_user_id to a VIEWER
        self.session.query(CohortUserStore) \
            .filter(CohortUserStore.user_id == self.owner_user_id) \
            .filter(CohortUserStore.cohort_id == self.cohort.id) \
            .update({'role': CohortUserRole.VIEWER})
        self.session.commit()

        # Adding a different CohortUser as owner
        new_cohort_user = CohortUserStore(
            cohort_id=self.cohort.id,
            role=CohortUserRole.OWNER
        )
        self.session.add(new_cohort_user)
        self.session.commit()

        response = self.app.post('/cohorts/delete/{0}'.format(self.cohort.id))

        assert_equal(response.status_code, 200)
        assert_true(response.data.find('isRedirect') >= 0)
        assert_true(response.data.find('/cohorts/') >= 0)
        cohort_id = self.cohort.id
        self.session.commit()

        # Check that all relevant rows are deleted
        cwu = self.session.query(CohortWikiUserStore) \
            .filter(CohortWikiUserStore.cohort_id == cohort_id) \
            .first()
        assert_not_equal(cwu, None)
        cu = self.session.query(CohortUserStore) \
            .filter(CohortUserStore.cohort_id == cohort_id) \
            .filter(CohortWikiUserStore.id == self.owner_user_id) \
            .first()
        assert_equal(cu, None)
        wu = self.session.query(WikiUserStore) \
            .filter(WikiUserStore.validating_cohort == cohort_id) \
            .first()
        assert_not_equal(wu, None)
        c = self.session.query(CohortStore).get(cohort_id)
        assert_not_equal(c, None)

    def test_delete_unauthorized_cohort(self):
        self.session.query(CohortUserStore).delete()
        self.session.commit()
        response = self.app.post('/cohorts/delete/{0}'.format(self.cohort.id))

        assert_true(response.data.find('isError') >= 0)
        assert_true(response.data.find('No role found in cohort user.') >= 0)

    def test_delete_empty_cohort(self):
        response = self.app.get('/cohorts/list/')
        response = json.loads(response.data)
        assert_equal(len(response['cohorts']), 1)

        self.session.query(CohortWikiUserStore).delete()
        self.session.query(WikiUserStore).delete()
        self.session.commit()
        cohort_id = self.cohort.id
        response = self.app.post('/cohorts/delete/{0}'.format(self.cohort.id))

        assert_true(response.data.find('isRedirect') >= 0)
        assert_true(response.data.find('/cohorts') >= 0)
        self.session.commit()

        c = self.session.query(CohortStore).get(cohort_id)
        assert_equal(c, None)

        response = self.app.get('/cohorts/list/')
        response = json.loads(response.data)
        assert_equal(len(response['cohorts']), 0)

    def test_add_new_tag(self):
        unparsed_tag = "  saMPLE tag  with BAD FORMatting   "
        response = self.app.post('/cohorts/{0}/tag/add/{1}'
                                 .format(self.cohort.id, unparsed_tag))
        assert_true(response.data.find('"tags":') >= 0)
        assert_true(response.data.find('"name": "sample-tag-with-bad-formatting"') >= 0)
        self.session.commit()

        t = self.session.query(TagStore.id) \
            .filter(TagStore.name == 'sample-tag-with-bad-formatting') \
            .first()
        assert_not_equal(t, None)
        ct = self.session.query(CohortTagStore) \
            .filter(CohortTagStore.cohort_id == self.cohort.id) \
            .filter(CohortTagStore.tag_id == t[0]) \
            .first()
        assert_not_equal(ct, None)
   
    def test_add_empty_tag(self):
        response = self.app.post('/cohorts/{0}/tag/add/'
                                 .format(self.cohort.id))
        assert_true(response.data.find('"You cannot submit an empty tag."') >= 0)

    def test_add_existing_tag(self):
        duplicate_tag = "duplicate-tag"
        tag = TagStore(
            name=duplicate_tag
        )
        self.session.add(tag)
        self.session.commit()
        response = self.app.post('/cohorts/{0}/tag/add/{1}'
                                 .format(self.cohort.id, duplicate_tag))
        assert_true(response.data.find('"tags":') >= 0)
        assert_true(response.data.find('"name": "{0}"'.format(duplicate_tag)) >= 0)
        tag_count = self.session.query(TagStore) \
            .filter(TagStore.name == duplicate_tag) \
            .count()
        assert_equal(tag_count, 1)


class CohortsControllerUploadTest(WebTest):
    def setUp(self):
        WebTest.setUp(self)
        self.cohort_service = CohortService()

    def test_get_upload_form(self):
        response = self.app.get('/cohorts/upload')
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('<h3>Create a Cohort') >= 0)

    def test_upload_invalid_form(self):
        response = self.app.post('/cohorts/upload')
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('<h3>Create a Cohort') >= 0)
        assert_true(response.data.find('Please fix validation problems') >= 0)

    def test_upload_taken_cohort_name(self):
        response = self.app.post('/cohorts/upload', data=dict(
            name=self.cohort.name,
            project='wiki',
            csv='just has to be set to something for this test',
            validate_as_user_ids='True',
        ))
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('<h3>Create a Cohort') >= 0)
        assert_true(response.data.find('That Cohort name is already taken') >= 0)

    def test_upload_works(self):
        response = self.app.post('/cohorts/upload', data=dict(
            name='new_cohort_name',
            project='wiki',
            csv=(StringIO('actual validation tested elsewhere'), 'cohort.csv'),
            validate_as_user_ids='True',
        ))
        assert_equal(response.status_code, 302)
        assert_true(response.data.find('href="/cohorts/#') >= 0)

    def test_paste_username_works(self):
        response = self.app.post('/cohorts/upload', data=dict(
            name='new_cohort_name',
            project='wiki',
            paste_username='actual validation tested elsewhere',
            validate_as_user_ids='True',
        ))
        assert_equal(response.status_code, 302)
        assert_true(response.data.find('href="/cohorts/#') >= 0)

    def test_upload_raises_exception(self):
        response = self.app.post('/cohorts/upload', data=dict(
            name='new_cohort_name',
            project='wiki',
            csv='not a file',
            validate_as_user_ids='True',
        ))
        assert_true(response.data.find('Server error while processing your upload') >= 0)

    def test_invalid_wiki_user_view(self):
        invalid = self.session.query(WikiUserStore).first()
        invalid.valid = False
        invalid.reason_invalid = 'check for this in an assert'
        self.session.commit()
        with cohort_service_set(app, self.cohort_service):
            response = self.app.get('/cohorts/detail/invalid-users/{0}'.format(
                self.cohort.id
            ))
        assert_equal(response.status_code, 200)
        assert_true(response.data.find(invalid.mediawiki_username) >= 0)
        assert_true(response.data.find(invalid.reason_invalid) >= 0)

    def test_invalid_wiki_user_view_works_when_cohort_invalid(self):
        self.helper_reset_validation()
        self.test_invalid_wiki_user_view()

    def test_invalid_wiki_user_view_error(self):
        response = self.app.get('/cohorts/detail/invalid-users/0')
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('Error fetching invalid users for') >= 0)

    def test_both_upload_and_paste_usernames(self):
        response = self.app.post('/cohorts/upload', data=dict(
            name='new_cohort_name',
            project='wiki',
            csv=(StringIO('actual validation tested elsewhere'), 'cohort.csv'),
            paste_username=('actual validation tested elsewhere'),
            validate_as_user_ids='True',
        ))
        assert_equal(response.status_code, 200)
        assert_true(response.data.find('<h3>Create a Cohort') >= 0)
        assert_true(response.data.find('Please fix validation problems') >= 0)
