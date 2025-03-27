# -*- coding: utf-8 -*-
import unittest
import sys
import os


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)


from hierosoft import (
    # echo0,
    # set_verbosity,
    find_by_value,
)


# MY_DIR = os.path.dirname(os.path.realpath(__file__))
# MODULE_DIR = os.path.dirname(MY_DIR)
# TEST_DATA_DIR = os.path.join(MY_DIR, "data")

# assert os.path.isdir(TEST_DATA_DIR)

class TestAlgorithms(unittest.TestCase):
    """Test only mixed-data (not just string/byte/bytearray) algorithms
    For string/bytes/bytearray functions, see test_morebytes instead
    """
    def test_find_by_value(self):
        l = [
            {
                'name': 'Bo',
                'id': 100
            },
            {
                'name': 'Bill',
                'id': 101
            },
            {
                'name': None,
                'id': 102
            },
            {
                'name': 'Jo',
                'id': 103
            },
            {
                'name': 'Jo',
                'id': 104
            },
        ]
        i = find_by_value(l, 'name', 'Jo')
        self.assertEqual(i, 3)
        self.assertEqual(l[i]['id'], 103)


if __name__ == "__main__":
    # testcase = TestAlgorithms()
    # for name in dir(testcase):
    #     if name.startswith("test"):
    #         fn = getattr(testcase, name)
    #         fn()  # Look at def test_* for the code if tracebacks start here
    # ^ constructor fails on Python 2 after tests run:
    #   ValueError: no such test method in <class '__main__.TestAlgorithms'>: runTest
    #   so:
    unittest.main()