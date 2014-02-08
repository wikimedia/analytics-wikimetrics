from subprocess import Popen
from os import devnull
from signal import SIGINT
from time import sleep

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
                  '--override-config', 'wikimetrics/config/test_config.yaml']
    celery_sched_cmd = ['wikimetrics', '--mode', 'scheduler', '--override-config',
                        'wikimetrics/config/test_config.yaml']
    global celery_proc
    celery_proc = Popen(celery_cmd, stdout=celery_out, stderr=celery_out)
    
    global celery_sched_proc
    celery_sched_proc = Popen(celery_sched_cmd, stdout=celery_out, stderr=celery_out)
    
    # wait until celery broker / worker is up
    tries = 0
    while(not celery_is_alive() and tries < 20):
        tries += 1
        sleep(0.5)


def tearDown():
    global celery_proc
    global celery_sched_proc
    
    if celery_proc is not None:
        celery_proc.send_signal(SIGINT)
    
    if celery_sched_proc is not None:
        celery_sched_proc.send_signal(SIGINT)


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
