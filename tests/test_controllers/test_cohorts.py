# -*- coding:utf-8 -*-
import json
from nose.tools import assert_equal, raises, assert_true, assert_false
from tests.fixtures import WebTest
from wikimetrics.controllers.cohorts import (
    parse_username,
    parse_records,
    normalize_user,
    normalize_newlines,
    normalize_project,
    to_safe_json,
    get_wikiuser_by_name,
    get_wikiuser_by_id,
    project_name_for_link,
    link_to_user_page,
    validate_records,
)
from wikimetrics.models import Cohort, CohortUser, CohortUserRole


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
    
    def test_full_detail(self):
        response = self.app.get('/cohorts/detail/{0}?full_detail=true'.format(
            self.cohort.id
        ))
        parsed = json.loads(response.data)
        assert_equal(response.status_code, 200)
        assert_equal(len(parsed['wikiusers']), 4)
    
    def test_validate_username(self):
        # this username has a few problems that the normalize call should handle
        # 1. normal ascii space in front
        # 2. lowercase
        # 3. nasty trailing unicode space (the reason this file has coding:utf-8)
        problem_username = ' editor test-specific-0 '
        
        parsed_user = parse_username(problem_username, decode=False)
        valid_user = normalize_user(parsed_user, 'enwiki')
        assert_equal(valid_user[0], self.editors[0].user_id)
        assert_equal(valid_user[1], 'Editor test-specific-0')
    
    def test_cohort_upload_finish_existing_name(self):
        response = self.app.post('/cohorts/create', data=dict(
            name=self.cohort.name,
        ))
        assert_true(response.data.find('isError') >= 0)
        assert_true(response.data.find('There was a problem') >= 0)
    
    def test_cohort_upload_finish_no_users_error(self):
        response = self.app.post('/cohorts/create', data=dict(
            name='blijalsijelij',
            project='enwiki',
            description='test',
            users='',  # invalid JSON should throw an error
        ))
        assert_true(response.data.find('isError') >= 0)
        assert_true(response.data.find('There was a problem') >= 0)
    
    def test_cohort_upload_finish_no_project_error(self):
        users = '''[
            {"username":"Dan","user_id":1,"project":"en"},
            {"username":"Stefan","user_id":2,"project":"ar"}
        ]'''
        response = self.app.post('/cohorts/create', data=dict(
            name='blijalsijelij',
            description='test',
            users=users,
        ))
        assert_true(response.data.find('isError') >= 0)
        assert_true(response.data.find('If all the users do not belong') >= 0)
    
    def test_cohort_upload_finish(self):
        new_cohort_name = 'New Test Cohort'
        new_cohort_description = 'test enwiki cohort'
        users = '''[
            {{"username":"Dan","project":"enwiki","user_id":{0}}},
            {{"username":"Evan","project":"dewiki","user_id":{1}}}
        ]'''.format(
            self.editors[0].user_id,
            self.editors[1].user_id,
        )
        response = self.app.post('/cohorts/create', data=dict(
            name=new_cohort_name,
            description=new_cohort_description,
            project='enwiki',
            users=users,
        ))
        assert_true(response.data.find('isRedirect') >= 0)
        assert_true(response.data.find('/cohorts/') >= 0)
        
        # look for the newly created cohort
        self.session.commit()
        cohort = self.session.query(Cohort).filter(Cohort.name == new_cohort_name).one()
        assert_equal(cohort.description, new_cohort_description)
    
    def test_cohort_upload_finish_sets_project_from_users(self):
        new_cohort_name = 'New Test Cohort'
        new_cohort_description = 'test enwiki cohort'
        users = '''[
            {{"username":"Dan","project":"enwiki","user_id":{0}}},
            {{"username":"Evan","project":"enwiki","user_id":{1}}}
        ]'''.format(
            self.editors[0].user_id,
            self.editors[1].user_id,
        )
        self.app.post('/cohorts/create', data=dict(
            name=new_cohort_name,
            description=new_cohort_description,
            users=users,
        ))
        
        # look for the newly created cohort
        self.session.commit()
        cohort = self.session.query(Cohort).filter(Cohort.name == new_cohort_name).one()
        assert_equal(cohort.default_project, 'enwiki')
    
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
        response = self.app.get('/cohorts/validate/project?project=enwiki')
        
        assert_equal(response.status_code, 200)
        assert_equal(json.loads(response.data), True)
    
    def test_normalize_newlines(self):
        stream = [
            'blahblah\r',
            'blahblahblahnor',
            'blahblah1\rblahblah2',
        ]
        lines = list(normalize_newlines(stream))
        assert_equal(len(lines), 5)
        assert_equal(lines[0], 'blahblah')
        assert_equal(lines[1], '')
        assert_equal(lines[2], 'blahblahblahnor')
        assert_equal(lines[3], 'blahblah1')
        assert_equal(lines[4], 'blahblah2')
    
    def test_to_safe_json(self):
        unsafe_json = '{"quotes":"He''s said: \"Real Artists Ship.\""}'
        safe_json = to_safe_json(unsafe_json)
        
        assert_equal(
            safe_json,
            '\\"{\\\\"quotes\\\\":\\\\"Hes said: \\\\"Real Artists Ship.\\\\"\\\\"}\\"'
        )
    
    def test_parse_records_with_project(self):
        parsed = parse_records(
            [
                ['dan', 'enwiki']
            ],
            None
        )
        assert_equal(len(parsed), 1)
        assert_equal(parsed[0]['username'], 'Dan')
        assert_equal(parsed[0]['raw_username'], 'Dan')
        assert_equal(parsed[0]['project'], 'enwiki')
    
    def test_parse_records_without_project(self):
        parsed = parse_records(
            [
                ['dan']
            ],
            'enwiki'
        )
        assert_equal(len(parsed), 1)
        assert_equal(parsed[0]['username'], 'Dan')
        assert_equal(parsed[0]['raw_username'], 'Dan')
        assert_equal(parsed[0]['project'], 'enwiki')
    
    def test_parse_records_with_shorthand_project(self):
        parsed = parse_records(
            [
                ['dan', 'en']
            ],
            None
        )
        assert_equal(len(parsed), 1)
        assert_equal(parsed[0]['username'], 'Dan')
        assert_equal(parsed[0]['raw_username'], 'Dan')
        assert_equal(parsed[0]['project'], 'en')
    
    def test_parse_records_with_utf8(self):
        parsed = parse_records(
            [
                # TODO: use weird characters U+0064	d	&#100;
                [u'dan', 'en']
            ],
            None
        )
        assert_equal(len(parsed), 1)
        assert_equal(parsed[0]['username'], 'Dan')
        assert_equal(parsed[0]['raw_username'], 'Dan')
        assert_equal(parsed[0]['project'], 'en')
    
    def test_normalize_project_shorthand(self):
        normal = normalize_project('en')
        assert_equal(normal, 'enwiki')
    
    def test_normalize_project_uppercase(self):
        normal = normalize_project('ENWIKI')
        assert_equal(normal, 'enwiki')
    
    def test_normalize_project_nonexistent(self):
        normal = normalize_project('blah')
        assert_equal(normal, None)
    
    def test_get_wikiuser_by_name(self):
        user = get_wikiuser_by_name('Editor test-specific-0', 'enwiki')
        assert_equal(user.user_name, 'Editor test-specific-0')
    
    def test_get_wikiuser_by_name_nonexistent(self):
        nonexistent = get_wikiuser_by_name('blahblahblah', 'enwiki')
        assert_equal(nonexistent, None)
    
    def test_get_wikiuser_by_id(self):
        user = get_wikiuser_by_id(self.editors[0].user_id, 'enwiki')
        assert_equal(user.user_name, self.editors[0].user_name)
    
    def test_get_wikiuser_by_id_nonexistent(self):
        nonexistent = get_wikiuser_by_id(123124124, 'enwiki')
        assert_equal(nonexistent, None)
    
    def test_normalize_user_by_name(self):
        normalized_user = normalize_user('Editor test-specific-0', 'enwiki')
        assert_equal(normalized_user[0], self.editors[0].user_id)
        assert_equal(normalized_user[1], self.editors[0].user_name)
    
    def test_normalize_user_by_name_nonexistent(self):
        normalized_user = normalize_user('DanNotExists', 'enwiki')
        assert_equal(normalized_user, None)
    
    def test_normalize_user_by_id(self):
        normalized_user = normalize_user(str(self.editors[0].user_id), 'enwiki')
        assert_equal(normalized_user[0], self.editors[0].user_id)
        assert_equal(normalized_user[1], self.editors[0].user_name)
    
    def test_normalize_user_by_id_nonexistent(self):
        normalized_user = normalize_user('123124124', 'enwiki')
        assert_equal(normalized_user, None)
    
    def test_project_name_for_link(self):
        project = project_name_for_link('en')
        assert_equal(project, 'en')
    
    def test_project_name_for_link_with_wiki(self):
        project = project_name_for_link('enwiki')
        assert_equal(project, 'en')
    
    def test_link_to_user_page(self):
        link = link_to_user_page('Dan has-spaces', 'en')
        assert_equal(link, 'https://en.wikipedia.org/wiki/User:Dan has-spaces')
    
    def test_link_to_user_page_unicode(self):
        link_to_user_page('ولاء عبد المنعم', 'ar')
        # just want to make sure no exceptions are raised
        assert_true(True)
    
    def test_validate_records(self):
        (valid, invalid) = validate_records([
            {
                'project': 'enwiki',
                'username': 'Editor test-specific-0',
                'raw_username': 'Editor test-specific-0',
            },
            {
                'project': 'blah',
                'username': 'Editor test-specific-0',
                'raw_username': 'Editor test-specific-0',
            },
            {
                'project': 'enwiki',
                'username': 'blah',
                'raw_username': 'blah',
            },
        ])
        
        assert_equal(len(valid), 1)
        assert_equal(len(invalid), 2)
        assert_equal(valid[0]['user_id'], self.editors[0].user_id)
        assert_equal(invalid[0]['reason_invalid'], 'invalid project: blah')
        assert_equal(invalid[1]['reason_invalid'], 'invalid user_name / user_id: blah')
