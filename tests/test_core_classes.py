import os
from unittest import TestCase
from nose.tools import assert_equals, assert_true
from nose.plugins.attrib import attr
from sqlalchemy.event import listen

from tests.fixtures import QueueTest, mediawiki_project
from wikimetrics.configurables import db, parse_db_connection_string, queue
from wikimetrics.database import get_host_projects, get_host_projects_map
from wikimetrics.schedules.daily import get_session_and_leave_open
from wikimetrics.models import ReportStore, MediawikiUser


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
    
    def test_db_session_always_fresh(self):
        s = db.get_session()
        try:
            r = ReportStore()
            s.add(r)
            s.commit()
            r.id = None
            s.commit()
        except:
            pass
        
        # if the session is not cleaned up properly, this will throw an exception
        s = db.get_session()
        s.execute('select 1').fetchall()
        
        s = db.get_mw_session(mediawiki_project)
        try:
            u = MediawikiUser()
            s.add(u)
            s.commit()
            u.user_id = None
            s.commit()
        except:
            pass
        
        # if the session is not cleaned up properly, this will throw an exception
        s = db.get_mw_session(mediawiki_project)
        s.execute('select 1').fetchall()
    
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


class SchedulerSetupTest(TestCase):
    def test_scheduler_configured(self):
        sched = queue.conf['CELERYBEAT_SCHEDULE']
        assert_equals(
            sched['update-daily-recurring-reports']['task'],
            'wikimetrics.schedules.daily.recurring_reports'
        )


class TestQueueOperation(QueueTest):
    def setUp(self):
        # make sure to create the wikimetrics engine
        db.get_session().close()
        QueueTest.setUp(self)
    
    def tearDown(self):
        QueueTest.tearDown(self)
    
    def test_every_task_gets_a_new_connection(self):
        """
        With our scoped sessions every task should receive a
        'new' high-level connection.
        It could be that this is a persistent connection
        as managed by mysql pool settings but it
        should be a new sqlalchemy object.
        
        There should only be one session per task.
        Note that the task we use below get_session_and_leave_open
        opens two sessions
        
        Testing how new connections and pool configuration interact
        is undeterministic and environment dependent so
        this test ensures that sqlalchemy is doing what it should
        when it comes to scoping celery connections but it does not
        test pool starvation.
        """
        global connections_opened
        connections_opened = 0
        tasks_to_execute = 10
        
        def increment_counter(connection, branch):
            global connections_opened
            connections_opened = connections_opened + 1
        listen(db.wikimetrics_engine, 'engine_connect', increment_counter)
        
        i = 0
        tasks = []
        while i <= tasks_to_execute:
            task = get_session_and_leave_open.apply_async()
            tasks.append(task)
            i += 1
        
        for t in tasks:
            t.get()
        assert_true(all([t.status for t in tasks]))
        assert_equals(connections_opened, tasks_to_execute + 1)
