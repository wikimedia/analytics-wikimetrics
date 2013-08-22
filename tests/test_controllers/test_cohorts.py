# -*- coding:utf-8 -*-
import json
from nose.tools import assert_equal, assert_not_equal, raises, assert_true
from tests.fixtures import WebTest
from wikimetrics.controllers.cohorts import (
    parse_username,
    normalize_user,
    normalize_newlines,
    to_safe_json,
)
from wikimetrics.models import Cohort


class TestCohortsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/cohorts/', follow_redirects=True)
        assert_equal(response.status_code, 200)
    
    def test_list(self):
        response = self.app.get('/cohorts/list', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            len(filter(lambda c : c['name'] == 'test_private', parsed['cohorts'])),
            1,
            '/cohorts/list should include a cohort named test_private, '
            'but instead returned:\n{0}'.format(response.data)
        )
    
    def test_detail(self):
        response = self.app.get('/cohorts/detail/{0}'.format(self.test_cohort_id))
        parsed = json.loads(response.data)
        assert_equal(response.status_code, 200)
        assert_equal(len(parsed['wikiusers']), 3)
    
    def test_detail_by_name(self):
        response = self.app.get('/cohorts/detail/{0}'.format(self.test_cohort_name))
        parsed = json.loads(response.data)
        assert_equal(response.status_code, 200)
        assert_equal(len(parsed['wikiusers']), 3)
    
    def test_full_detail(self):
        response = self.app.get('/cohorts/detail/{0}?full_detail=true'.format(
            self.test_cohort_id
        ))
        parsed = json.loads(response.data)
        assert_equal(response.status_code, 200)
        assert_equal(len(parsed['wikiusers']), 4)
    
    def test_validate_username(self):
        # this username has a few problems that the normalize call should handle
        # 1. normal ascii space in front
        # 2. lowercase
        # 3. nasty trailing unicode space (the reason this file has coding:utf-8)
        problem_username = ' dan '
        
        parsed_user = parse_username(problem_username, decode=False)
        valid_user = normalize_user(parsed_user, 'enwiki')
        assert_not_equal(valid_user, None)
    
    def test_get_cohort_by_name_not_found(self):
        response = self.app.get('/cohorts/detail/1-OI--LASJLI---LIJSL$EIOJ')
        assert_equal(response.status_code, 404)
    
    def test_get_cohort_by_id_not_found(self):
        response = self.app.get('/cohorts/detail/133715435033')
        assert_equal(response.status_code, 404)
    
    def test_cohort_upload_finish_existing_name(self):
        response = self.app.post('/cohorts/create', data=dict(
            name=self.test_cohort_name,
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
            self.test_mediawiki_user_id,
            self.test_mediawiki_user_id_evan,
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
        cohort = self.session.query(Cohort).filter(Cohort.name == new_cohort_name).one()
        assert_equal(cohort.description, new_cohort_description)
    
    def test_cohort_upload_finish_sets_project_from_users(self):
        new_cohort_name = 'New Test Cohort'
        new_cohort_description = 'test enwiki cohort'
        users = '''[
            {{"username":"Dan","project":"enwiki","user_id":{0}}},
            {{"username":"Evan","project":"enwiki","user_id":{1}}}
        ]'''.format(
            self.test_mediawiki_user_id,
            self.test_mediawiki_user_id_evan,
        )
        self.app.post('/cohorts/create', data=dict(
            name=new_cohort_name,
            description=new_cohort_description,
            users=users,
        ))
        
        # look for the newly created cohort
        cohort = self.session.query(Cohort).filter(Cohort.name == new_cohort_name).one()
        assert_equal(cohort.default_project, 'enwiki')
    
    def test_validate_cohort_name_allowed(self):
        response = self.app.get('/cohorts/validate/name?name={0}'.format(
            self.test_cohort_name)
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
