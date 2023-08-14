# -*- coding: utf-8 -*-
from __future__ import print_function
import unittest
import sys
import os

my_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(my_dir)
repo_dir = os.path.dirname(module_dir)

if __name__ == "__main__":
    sys.path.insert(0, repo_dir)

if sys.version_info.major < 3:
    print("[test_logging] using Python 2 shims for logging.",
          file=sys.stderr)
    import hierosoft.morelogging as logging
else:
    print("[test_logging] using Python 3 logging.",
          file=sys.stderr)
    import logging
from hierosoft.morelogging import (
    echo0,
    echo1,
    echo2,
    set_verbosity,
    to_syntax_error,
)


class TestLogging(unittest.TestCase):
    
    def __init__(self):
        if sys.version_info.major >=3:
            super().__init__(self)
        else:
            # unittest.TestCase.__init__(self)
            super(TestLogging, self).__init__()
    
    def test_to_syntax_error(self):
        
        '''
        self.assertEqual(
            to_syntax_error("no_file", None, "no_error"),
            "no_file: no_error",
        )
        self.assertEqual(
            to_syntax_error("no_file", 3, "no_error"),
            "no_file:3: no_error",
        )
        self.assertEqual(
            to_syntax_error("no_file", 3, "no_error", col=4),
            "no_file:3:4: no_error",
        )
        '''
        # ^ Now pycodetool uses in Python format by default such as for
        #   Geany, so instead do:
        self.assertEqual(
            to_syntax_error("no_file", None, "no_error"),
            'File "no_file", line  no_error',
            # TODO: improve behavior & test
        )
        self.assertEqual(
            to_syntax_error("no_file", 3, "no_error"),
            'File "no_file", line 3, no_error',
        )
        self.assertEqual(
            to_syntax_error("no_file", 3, "no_error", col=4),
            'File "no_file", line 3, 4 no_error',
            # TODO: Seek column if compatible w/ Geany etc. & test
        )

    def test_logging(self):
        """Test using morelogging in the same way as Python 3 logging.

        This code matches upstream example code (Python 3 logging) so it
        should not be changed. If upstream example code changes, then
        both this and future usage should be supported.
        """
        logging.basicConfig(filename='example.log', encoding='utf-8',
                            level=logging.DEBUG)
        logging.debug('This message should go to the log file')
        logging.info('So should this')
        logging.warning('And this, too')
        logging.error('And non-ASCII stuff, too, like Øresund and Malmö')

if __name__ == "__main__":
    testcase = TestLogging()
    for name in dir(testcase):
        if name.startswith("test"):
            fn = getattr(testcase, name)
            fn()  # Look at def test_* for the code if tracebacks start here
