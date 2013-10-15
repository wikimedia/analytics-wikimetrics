import os
from unittest import TestCase
from nose.tools import assert_equals, assert_true
from wikimetrics.configurables import db
from wikimetrics.database import get_host_projects, get_host_projects_map


class DatabaseSetupTest(TestCase):
    
    def test_get_host_projects(self):
        (host_one, projects) = get_host_projects(1)
        assert_equals(host_one, 1)
        assert_true('enwiki' in projects)
    
    def test_get_host_projects_map(self):
        project_host_map = get_host_projects_map()
        assert_true('enwiki' in project_host_map)
        assert_true('arwiki' in project_host_map)
        assert_true('commonswiki' in project_host_map)
    
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
