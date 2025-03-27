# -*- coding: utf-8 -*-
from __future__ import print_function
import unittest
import platform
import sys
import os

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

if sys.version_info.major < 3:
    print("[test_logging] using Python 2 shims for logging.",
          file=sys.stderr)
    import hierosoft.logging2 as logging
else:
    print("[test_logging] using Python 3 logging.",
          file=sys.stderr)
    import logging
from hierosoft.programinfo import (  # noqa: E402
    # echo0,
    # echo1,
    # echo2,
    # set_verbosity,
    split_version,
    path_split_all,
    ProgramInfo,
)



class TestProgramInfo(unittest.TestCase):

    # def __init__(self):
    #     if sys.version_info.major >=3:
    #         super().__init__()
    #     else:
    #         # unittest.TestCase.__init__(self)
    #         # super(TestProgramInfo, self).__init__()
    #         # Python 2.7.18 says:
    #         # "ValueError: no such test method in
    #         # <class '__main__.TestProgramInfo'>: runTest"
    #         # in either case!
    #         pass

    def test_path_split_all(self):
        if platform.system() == "Windows":
            self.assertEqual(path_split_all("C:\\users\\user"), ["C:", "users", "user"])
        else:
            self.assertEqual(path_split_all("/home/user/tmp"), ["/", "home", "user", "tmp"])

    def test_split_version(self):
        self.assertEqual(split_version("something"), ("something",))
        self.assertEqual(split_version("something-git"), ("something", "", "git"))
        self.assertEqual(split_version("something-6.0.0-git"), ("something", "6.0.0", "git"))
        self.assertEqual(split_version("something-6.0.0-1"), ("something", "6.0.0", "1"))
        self.assertEqual(split_version("something-6.0.0"), ("something", "6.0.0"))

    def test_program_info_version(self):
        program = ProgramInfo()
        self.assertEqual(split_version("Ardour-8.6.0"), ("Ardour", "8.6.0"))
        self.assertEqual(split_version("ardour8"), ("ardour8",))
        # ^ otherwise below won't work correctly
        program.set_version_from_path("/opt/Ardour-8.6.0/bin/ardour8")
        self.assertEqual(program.name, ("Ardour"))
        self.assertEqual(program.version, "8.6.0")
        self.assertEqual(program.version_tuple(), (8, 6, 0))
        self.assertEqual(program.suffix, None)
        program = ProgramInfo()
        program.set_version_from_path("/opt/Ardour/bin/ardour8")
        self.assertEqual(program.name, "ardour8")
        self.assertEqual(program.version, None)
        self.assertEqual(program.version_tuple(), None)
        self.assertEqual(program.suffix, None)
        program = ProgramInfo()
        program.set_version_from_path("/opt/Ardour/bin/ardour-8")
        self.assertEqual(program.name, "ardour")
        self.assertEqual(program.version, "8")
        self.assertEqual(program.version_tuple(), (8,))
        self.assertEqual(program.suffix, None)


if __name__ == "__main__":
    unittest.main()
    # testcase = TestProgramInfo()
    # for name in dir(testcase):
    #     if name.startswith("test"):
    #         fn = getattr(testcase, name)
    #         fn()  # Look at def test_* for the code if tracebacks start here
