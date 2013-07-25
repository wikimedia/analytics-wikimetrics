# -*- coding:utf-8 -*-
import pprint
import json
from nose.tools import assert_equal, assert_not_equal
from tests.fixtures import WebTest
from wikimetrics.controllers.cohorts import *


class TestCohortsController(WebTest):
    
    def test_index(self):
        response = self.app.get('/cohorts/', follow_redirects=True)
        assert_equal(
            response.status_code, 200,
            '/cohorts should get the list of cohorts'
        )
    
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
        response = self.app.get('/cohorts/detail/1', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            response.status_code,
            200,
        )
        assert_equal(
            len(parsed['wikiusers']),
            3,
            '/cohorts/detail/1 should return JSON object with key `wikiusers`'
            'for a list of length 3== `test`, but instead returned: {0}'.format(parsed)
        )
    
    def test_full_detail(self):
        response = self.app.get('/cohorts/detail/1?full_detail=true', follow_redirects=True)
        parsed = json.loads(response.data)
        assert_equal(
            response.status_code,
            200,
        )
        assert_equal(
            len(parsed['wikiusers']),
            4,
            '/cohorts/detail/1 should return JSON object with key `wikiusers`'
            'for a list of length 4== `test`, but instead returned: {0}'.format(parsed)
        )
    
    def test_not_found(self):
        response = self.app.get('/cohorts/detail/no_way_anybody_names_a_cohort_this_23982739873')
        
        assert_equal(
            response.status_code,
            404,
        )
    
    def test_validate_username(self):
        # this username has a few problems that the normalize call should handle
        # 1. normal ascii space in front
        # 2. lowercase
        # 3. nasty trailing unicode space (the reason this file has an encoding definition)
        problem_username = ' dan '
        
        parsed_user = parse_username(problem_username)
        valid_user = normalize_user(parsed_user, 'enwiki')
        assert_not_equal(valid_user, None)
