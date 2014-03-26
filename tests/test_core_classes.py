import os
from unittest import TestCase
from nose.tools import assert_equals, assert_true
from wikimetrics.configurables import db, parse_db_connection_string
from wikimetrics.database import get_host_projects, get_host_projects_map


class DatabaseSetupTest(TestCase):
    """"
    These tests access the 'live' project_host_map
    thus they make an http connection to get it.
    The rest of the tests should would offline as they do not access
    the function get_host_projects directly.
    """
    def test_get_host_projects(self):
        (host_one, projects) = get_host_projects(1)
        assert_equals(host_one, 1)
        assert_true('enwiki' in projects)

    def test_get_host_projects_map(self):
        project_host_map = get_host_projects_map()
        assert_true('enwiki' in project_host_map)
        assert_true('dewiki' in project_host_map)

    def test_parse_db_connection_string(self):
        url = 'mysql://wikimetrics:wikimetrics@localhost/wikimetrics'
        user, password, host, dbName = parse_db_connection_string(url)
        assert_equals(user, 'wikimetrics')
        assert_equals(password, 'wikimetrics')
        assert_equals(host, 'localhost')
        assert_equals(dbName, 'wikimetrics')



    #def test_get_fresh_project_host_map(self):
        #project_host_map_cache_file = 'project_host_map.json'
        ## make sure any cached file is deleted
        #if os.path.exists(project_host_map_cache_file):
        #os.remove(project_host_map_cache_file)

        #db.get_project_host_map(usecache=True)
        #assert_true(os.path.exists(project_host_map_cache_file))

        #os.remove(project_host_map_cache_file)
        #db.get_project_host_map(usecache=False)
        #assert_true(os.path.exists(project_host_map_cache_file))
