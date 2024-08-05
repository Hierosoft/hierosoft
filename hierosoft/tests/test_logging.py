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
    pformat,
    human_readable,
)


class TestLogging(unittest.TestCase):

    # def __init__(self):
    #     if sys.version_info.major >=3:
    #         super().__init__()
    #     else:
    #         # unittest.TestCase.__init__(self)
    #         # super(TestLogging, self).__init__()
    #         # Python 2.7.18 says:
    #         # ValueError: no such test method in <class '__main__.TestLogging'>: runTest
    #         # in either case!
    #         pass

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

    def test_mimic_logging_module(self):
        self.assertEqual(logging.CRITICAL, 50)

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

    def test_pformat(self):
        bs = "\x08"
        bss = "\\x08"  # The replacement generated by CPython
        pformat_bss = "\\b"  # The replacement generated by morelogging
        self.assertEqual("\b", bs)  # If fails, change bs *and* bss
        self.assertEqual(pformat("\bHello"), '"'+pformat_bss+'Hello"')
        self.assertEqual(pformat(
            "\bHello",
            escape_if_like_str=False,
        ), '"\bHello"')
        self.assertEqual(pformat(
            "\bHello",
            escape_if_like_str=False,
            quote_if_like_str=False,
        ), "\bHello")
        self.assertEqual(pformat("Hello\r\n"), '"Hello\\r\\n"')
        self.assertEqual(pformat("Hello\t"), '"Hello\\t"')

    def test_human_readable(self):
        self.assertEqual(human_readable(512), "512bytes")
        self.assertEqual(human_readable(1024), "1KB")
        self.assertEqual(human_readable(1024*1024), "1MB")
        self.assertEqual(human_readable(1024*1024*1024), "1GB")
        self.assertEqual(human_readable(1024*1024*1024*1024), "1TB")
        self.assertEqual(human_readable(8192), "8KB")
        self.assertEqual(human_readable(8192*1024), "8MB")
        self.assertEqual(human_readable(8192*1024*1024), "8GB")
        self.assertEqual(human_readable(8192*1024*1024*1024), "8TB")

if __name__ == "__main__":
    unittest.main()
    # testcase = TestLogging()
    # for name in dir(testcase):
    #     if name.startswith("test"):
    #         fn = getattr(testcase, name)
    #         fn()  # Look at def test_* for the code if tracebacks start here
