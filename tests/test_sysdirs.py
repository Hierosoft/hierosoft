import os
import sys
import unittest

from datetime import datetime

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

from hierosoft.sysdirs import sysdirs


class TestMorePlatform(unittest.TestCase):
    """Test only mixed-data (not just string/byte/bytearray) algorithms
    For string/bytes/bytearray functions, see test_morebytes instead
    """
    def test_home(self):
        self.assertEqual(sysdirs['HOME'], os.path.expanduser("~"))
        # As for other keys, we can only test paths that are same on
        #   every platform, unless platform is imported for the test(s)
        #   to change test behavior by platform.
        with self.assertRaises(TypeError, msg="Should be readonly but allowed setitem"):
            sysdirs['HOME'] = ""


if __name__ == "__main__":
    unittest.main()
