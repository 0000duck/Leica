# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 16:05:49 2018

@author: peter
"""
import logging
import time
import unittest

from CESAPI.command import *
from CESAPI.connection import Connection
from CESAPI.test import LTSimulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base class for most of the other test cases. Used to setup and teardown
# the LTSimulator instance that the test cases use.
class CommandTestCase(unittest.TestCase):
    def __init(self):
        self.sim = None

    def setUp(self):
        self.sim = LTSimulator()
        self.sim.start()

    def tearDown(self):
        self.sim.stop()
        self.sim.join()

# Send an InitializeCT packet and verify that an InitializeRT packet was returned.
class InitializeTestCase(CommandTestCase):
    def runTest(self):
        success = False
        connection = Connection()
        initrt = None
        try:
            connection.connect(host='localhost')
            command = CommandSync(connection)
            
            initrt = command.Initialize()
        except Exception as e:
            logger.debug(e)
        finally:
            if connection != None:
                connection.disconnect()

        self.assertFalse(initrt == None)
        self.assertEqual(ES_C_Initialize, initrt.packetInfo.command)

if __name__ == '__main__':
    unittest.main()