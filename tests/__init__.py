from subprocess import Popen
from os import devnull
from signal import SIGINT
from queue import celery_is_alive
from time import sleep


celery_proc = None


def setUp():
    # TODO configure celery verbosity
    celery_out = open(devnull, "w")
    celery_cmd = ['/usr/bin/python', 'queue.py', 'worker', '-l', 'debug']
    celery_proc = Popen(celery_cmd, stdout=celery_out, stderr=celery_out)

    # wait until celery broker / worker is up
    while(not celery_is_alive()):
        sleep(0.5)


def tearDown():
    if celery_proc is not None:
        celery_proc.send_signal(SIGINT)
