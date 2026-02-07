# -*- coding: utf-8 -*-
import os
import sys
import unittest

from datetime import datetime

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

from hierosoft.moresix import datetime_timestamp  # noqa:E402


class TestMoreSix(unittest.TestCase):
    """Test only mixed-data (not just string/byte/bytearray) algorithms
    For string/bytes/bytearray functions, see test_morebytes instead
    """
    def test_datetime_timestamp(self):
        good_dt_tuple = (2025, 3, 27, 15, 19, 21, 380898)
        good_dt = datetime(*good_dt_tuple)
        good_timestamp = 1743103161.380898
        good_python2_timestamp = float(round(good_timestamp))
        self.assertEqual(good_dt.year, 2025)
        self.assertEqual(good_dt.month, 3)
        self.assertEqual(good_dt.day, 27)
        if sys.version_info.major >= 3:
            got_timestamp = datetime_timestamp(good_dt)
            self.assertEqual(got_timestamp, good_timestamp)
            self.assertEqual(got_timestamp, good_dt.timestamp())
            got_py2_timestamp = datetime_timestamp(good_dt, emulate_python2=True)
            self.assertEqual(got_py2_timestamp, good_python2_timestamp)
        else:
            got_timestamp = datetime_timestamp(good_dt)
            self.assertEqual(got_timestamp, good_python2_timestamp)
            # datetime.datetime instance has no timestamp method in Python 2


if __name__ == "__main__":
    unittest.main()
