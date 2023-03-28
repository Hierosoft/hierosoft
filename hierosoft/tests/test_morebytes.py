# -*- coding: utf-8 -*-
import unittest
import sys
import os


my_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(my_dir)
repo_dir = os.path.dirname(module_dir)

if __name__ == "__main__":
    sys.path.insert(0, repo_dir)


from hierosoft import (
    echo0,
    set_verbosity,
)

from hierosoft.morebytes import (
    to_hex,
)


# MY_DIR = os.path.dirname(os.path.realpath(__file__))
# MODULE_DIR = os.path.dirname(MY_DIR)
# TEST_DATA_DIR = os.path.join(MY_DIR, "data")

# assert os.path.isdir(TEST_DATA_DIR)

class TestAlgorithms(unittest.TestCase):

    def test_to_hex(self):
        bytestring = "abcd".encode('utf-8')
        expected_s0 = '61626364'
        # ^ from Python 3.5+: "abcd".encode('utf-8').hex()
        expected_s1 = '61 62 63 64'
        # ^ from Python 3.5+: "abcd".encode('utf-8').hex(" ")
        self.assertEqual(to_hex(bytestring), expected_s0)
        self.assertEqual(to_hex(bytestring, delimiter=" "), expected_s1)


if __name__ == "__main__":
    testcase = TestAlgorithms()
    count = 0
    for name in dir(testcase):
        if name.startswith("test"):
            fn = getattr(testcase, name)
            fn()  # Look at def test_* for the code if tracebacks start here
            count += 1
    echo0("{} test(s) passed.".format(count))
