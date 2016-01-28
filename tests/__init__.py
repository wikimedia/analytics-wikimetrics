from subprocess import Popen
from os import devnull
from signal import SIGINT
from time import sleep
from wikimetrics.configurables import queue
from celery.utils import LOG_LEVELS

celery_proc = None
celery_sched_proc = None


def celery_is_alive():
    try:
        from celery.task.control import inspect
        insp = inspect()
        d = insp.stats()
        if d:
            return True
    except IOError:
        return False
    
    return False


def setUp():
    """
    Set global testing variables and override database names
    so they have "_testing" as a suffix
    """
    setUpTestingDB()
    
    celery_out = open(devnull, "w")
    # TODO have a more solid setup of celery for development
    #celery_out = open("/tmp/logCelery.txt", "w")
    celery_cmd = ['wikimetrics', '--mode', 'queue',
                  '--override-config', '/srv/wikimetrics/config/test_config.yaml']
    global celery_proc
    celery_proc = Popen(celery_cmd, stdout=celery_out, stderr=celery_out)
    
    # TODO remove from here when
    # this bug is fixed: https://bugzilla.wikimedia.org/show_bug.cgi?id=66770
    queue.conf['CELERY_ALWAYS_EAGER'] = True
    queue.conf['EAGER_PROPAGATES_EXCEPTION'] = True
    queue.conf.CELERYD_LOG_LEVEL = LOG_LEVELS['DEBUG']
    # wait until celery broker / worker is up
    tries = 0
    while(not celery_is_alive() and tries < 20):
        tries += 1
        sleep(0.5)


def tearDown():
    global celery_proc
    if celery_proc is not None:
        celery_proc.send_signal(SIGINT)


def setUpTestingDB():
    """
        Set global testing variables.
        By convention testing dbs are development dbs with sufix "_testing"
        we change url connection strings so tests run on testing databases
        Note that wikimetrics user already exists, puppet has created it.
    """
    # NOTE: need to import these inline, otherwise they might match the
    # nosetests regular expression and run as tests
    from wikimetrics.configurables import app, db, setup_testing_config
    # Set TESTING to true so we can know to not check CSRF
    # TODO we need a global config object
    app.config['TESTING'] = True
    db.config = setup_testing_config(db.config)
