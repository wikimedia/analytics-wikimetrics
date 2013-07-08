from subprocess import Popen
from os import devnull
from signal import SIGINT
from time import sleep


celery_proc = None


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


#def setUp():
    #celery_out = open(devnull, "w")
    #celery_cmd = ['wikimetrics', '--mode', 'celery']
    #global celery_proc
    #celery_proc = Popen(celery_cmd, stdout=celery_out, stderr=celery_out)
    
    ## wait until celery broker / worker is up
    #tries = 0
    #while(not celery_is_alive() and tries < 20):
        #tries += 1
        #sleep(0.5)


#def tearDown():
    #global celery_proc
    #if celery_proc is not None:
        #celery_proc.send_signal(SIGINT)
