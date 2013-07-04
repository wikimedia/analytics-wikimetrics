import io
import os
import unittest
from nose.tools import assert_equals
from wikimetrics.configurables import create_object_from_config_file


class ConfigurationTest(unittest.TestCase):
    
    TEST_CONFIG = 'wikimetrics_test_configuration_file.py'
    
    def setUp(self):
        f = io.open(self.TEST_CONFIG, 'w')
        f.write(u'TEST_SETTING=2')
        f.close()
    
    def tearDown(self):
        os.remove(self.TEST_CONFIG)
    
    def test_create_object_from_config_file(self):
        obj = create_object_from_config_file(self.TEST_CONFIG)
        
        assert_equals(obj.TEST_SETTING, 2, 'The configuration file was not read properly')
