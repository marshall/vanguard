import logging
import os
import sys
import unittest

logger = logging.getLogger('tests')

this_dir = os.path.dirname(os.path.abspath(__file__))
top_dir = os.path.dirname(this_dir)
sys.path.append(top_dir)

def load_tests(loader, standard_tests, pattern):
    import vanguard.log as log
    log.setup(filename='/tmp/vanguard-test.log', debug_stdout=True)

    package_tests = loader.discover(start_dir=this_dir, pattern='test*.py')
    standard_tests.addTests(package_tests)
    return standard_tests
