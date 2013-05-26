from nose.tools import *

def blah():
    raise(Exception('aaah!'))

def test_job_maps_correctly_to_db():
    #assert_raises(Exception, blah, 2, "i don't read the docs")
    ok_(False, "i don't read the docs")
