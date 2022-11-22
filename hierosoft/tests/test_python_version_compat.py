# -*- coding: utf-8 -*-
import unittest
import sys
import os

my_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(my_dir)
repo_dir = os.path.dirname(module_dir)

if __name__ == "__main__":
    sys.path.insert(0, repo_dir)

from hierosoft.logging import (
    echo0,
    echo1,
    echo2,
    set_verbosity,
    to_syntax_error,
)

from hierosoft import (
    s2or3,
)


class TestPythonVersionCompat(unittest.TestCase):
    def test_s2or3(self):
        tmp_firmware_data = bytes("abcdef", encoding='utf-8')
        data = s2or3(tmp_firmware_data)
        good_opener = "abc"
        bad_opener = "x"
        ok = False
        if data.startswith(good_opener):
            # ^ better not raise:
            #   "TypeError: startswith first arg must be bytes or a
            #   tuple of bytes, not str"
            ok = True
        self.assertTrue(ok)
        startswith_even_though_didnt_match = False
        if data.startswith(bad_opener):
            startswith_even_though_didnt_match = True
        self.assertTrue(not startswith_even_though_didnt_match)


if __name__ == "__main__":
    testcase = TestPythonVersionCompat()
    for name in dir(testcase):
        if name.startswith("test"):
            fn = getattr(testcase, name)
            fn()  # Look at def test_* for the code if tracebacks start here
