import json
import time
from StringIO import StringIO
from nose.tools import assert_equal, assert_not_equal, assert_true, assert_false
from wikimetrics.configurables import app
from tests.fixtures import WebTest
from wikimetrics.models import (
    Cohort, CohortUser, CohortUserRole, ValidateCohort,
    CohortWikiUser, WikiUser, User
)


class CohortsControllerTest(WebTest):
    
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
            Cohort(name='c1', enabled=True, validated=False),
            Cohort(name='c2', enabled=True, validated=True)
        ]
        self.session.add_all(cohorts)
        self.session.commit()
        owners = [
            CohortUser(
                cohort_id=c.id,
                user_id=self.owner_user_id,
                role=CohortUserRole.OWNER
            )
            for c in cohorts
        ]
        self.session.add_all(owners)
        self.session.commit()
        
        response = self.app.get('/cohorts/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(len(parsed['cohorts']), 2)
        assert_false('c1' in [c['name'] for c in parsed['cohorts']])
        assert_true('c2' in [c['name'] for c in parsed['cohorts']])
    
    def test_detail(self):
        response = self.app.get('/cohorts/detail/{0}'.format(self.cohort.id))
        parsed = json.loads(response.data)
        assert_equal(response.status_code, 200)
        assert_equal(len(parsed['wikiusers']), 3)
    
    def test_detail_by_name(self):
        response = self.app.get('/cohorts/detail/{0}'.format(self.cohort.name))
        parsed = json.loads(response.data)
        assert_equal(response.status_code, 200)
        assert_equal(len(parsed['wikiusers']), 3)
        # this cohort did not go through async validation
        assert_equal(parsed['validation_status'], 'UNKNOWN')
        assert_equal(parsed['validated_count'], 3)
        assert_equal(parsed['total_count'], 3)
    
    def test_detail_by_name_after_async_validate(self):
        self.helper_reset_validation()
        validate_cohort = ValidateCohort(self.cohort)
        async_result = validate_cohort.task.delay(validate_cohort)
        self.cohort.validation_queue_key = async_result.task_id
        async_result.get()
        
        response = self.app.get('/cohorts/detail/{0}'.format(self.cohort.name))
        parsed = json.loads(response.data)
        assert_equal(parsed['validation_status'], 'SUCCESS')
        assert_equal(parsed['validated_count'], 4)
        assert_equal(parsed['total_count'], 4)
    
    def test_full_detail(self):
        response = self.app.get('/cohorts/detail/{0}?full_detail=true'.format(
            self.cohort.id
        ))
        parsed = json.loads(response.data)
        assert_equal(response.status_code, 200)
        assert_equal(len(parsed['wikiusers']), 4)
    
    def test_detail_not_allowed(self):
        self.helper_remove_authorization()
        response = self.app.get('/cohorts/detail/{0}'.format(self.cohort.id))
        assert_equal(response.status_code, 401)
        assert_equal(response.data, 'You are not allowed to access this Cohort')
    
    def test_detail_not_found(self):
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
        response = self.app.post('/cohorts/validate/0')
        
        assert_true(response.data.find('isError') >= 0)
        assert_true(response.data.find('This cohort does not exist') >= 0)
    
    def test_validate_unauthorized_cohort(self):
        self.helper_remove_authorization()
        response = self.app.post('/cohorts/validate/{0}'.format(self.cohort.id))
        
        assert_true(response.data.find('isError') >= 0)
        assert_true(response.data.find('You are not allowed to access this cohort') >= 0)
    
    def test_validate_cohort_again_after_upload(self):
        self.helper_reset_validation()
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
        cwu = self.session.query(CohortWikiUser) \
            .filter(CohortWikiUser.cohort_id == cohort_id) \
            .first()
        assert_equal(cwu, None)
        cu = self.session.query(CohortUser) \
            .filter(CohortUser.cohort_id == cohort_id) \
            .filter(CohortUser.user_id == self.owner_user_id) \
            .first()
        assert_equal(cu, None)
        wu = self.session.query(WikiUser) \
            .filter(WikiUser.validating_cohort == cohort_id) \
            .first()
        assert_equal(wu, None)
        c = self.session.query(Cohort).get(cohort_id)
        assert_equal(c, None)

    def test_delete_cohort_owner_has_viewer(self):
        viewer_user = User()
        self.session.add(viewer_user)
        self.session.commit()

        viewer_cohort_user = CohortUser(
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
        cwu = self.session.query(CohortWikiUser) \
            .filter(CohortWikiUser.cohort_id == cohort_id) \
            .first()
        assert_equal(cwu, None)
        cu = self.session.query(CohortUser) \
            .filter(CohortUser.cohort_id == cohort_id) \
            .first()
        assert_equal(cu, None)
        wu = self.session.query(WikiUser) \
            .filter(WikiUser.validating_cohort == cohort_id) \
            .first()
        assert_equal(wu, None)
        c = self.session.query(Cohort).get(cohort_id)
        assert_equal(c, None)

    def test_delete_cohort_as_viewer(self):
        # Changing the owner_user_id to a VIEWER
        self.session.query(CohortUser) \
            .filter(CohortUser.user_id == self.owner_user_id) \
            .filter(CohortUser.cohort_id == self.cohort.id) \
            .update({'role': CohortUserRole.VIEWER})
        self.session.commit()

        # Adding a different CohortUser as owner
        new_cohort_user = CohortUser(
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
        cwu = self.session.query(CohortWikiUser) \
            .filter(CohortWikiUser.cohort_id == cohort_id) \
            .first()
        assert_not_equal(cwu, None)
        cu = self.session.query(CohortUser) \
            .filter(CohortUser.cohort_id == cohort_id) \
            .filter(CohortWikiUser.id == self.owner_user_id) \
            .first()
        assert_equal(cu, None)
        wu = self.session.query(WikiUser) \
            .filter(WikiUser.validating_cohort == cohort_id) \
            .first()
        assert_not_equal(wu, None)
        c = self.session.query(Cohort).get(cohort_id)
        assert_not_equal(c, None)

    def test_delete_unauthorized_cohort(self):
        self.session.query(CohortUser).delete()
        self.session.commit()
        response = self.app.post('/cohorts/delete/{0}'.format(self.cohort.id))

        assert_true(response.data.find('isError') >= 0)
        assert_true(response.data.find('No role found in cohort user.') >= 0)

    def test_delete_empty_cohort(self):
        response = self.app.get('/cohorts/list/')
        response = json.loads(response.data)
        assert_equal(len(response['cohorts']), 1)

        self.session.query(CohortWikiUser).delete()
        self.session.query(WikiUser).delete()
        self.session.commit()
        cohort_id = self.cohort.id
        response = self.app.post('/cohorts/delete/{0}'.format(self.cohort.id))

        assert_true(response.data.find('isRedirect') >= 0)
        assert_true(response.data.find('/cohorts') >= 0)
        self.session.commit()

        c = self.session.query(Cohort).get(cohort_id)
        assert_equal(c, None)

        response = self.app.get('/cohorts/list/')
        response = json.loads(response.data)
        assert_equal(len(response['cohorts']), 0)


class CohortsControllerUploadTest(WebTest):
    
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
        invalid = self.session.query(WikiUser).first()
        invalid.valid = False
        invalid.reason_invalid = 'check for this in an assert'
        self.session.commit()
        response = self.app.get('/cohorts/detail/invalid-users/{0}'.format(
            self.cohort.id
        ))
        assert_equal(response.status_code, 200)
        assert_true(response.data.find(invalid.mediawiki_username) >= 0)
        assert_true(response.data.find(invalid.reason_invalid) >= 0)
    
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
