import os
import sys
import unittest

from datetime import datetime

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(TESTS_DIR)

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

from hierosoft.readonlydict import ReadOnlyOrderedDict


class TestReadOnlyDict(unittest.TestCase):
    """Test only mixed-data (not just string/byte/bytearray) algorithms
    For string/bytes/bytearray functions, see test_morebytes instead
    """
    def test_readonly_ordered_dict(self):
        od = ReadOnlyOrderedDict()
        od['b'] = 2
        od['a'] = 1
        od['c'] = 0
        prev_value = None
        for k, v in od.items():
            if prev_value is not None:
                self.assertLess(v, prev_value)
            prev_value = v
        self.assertEqual(len(od), 3)
        od.readonly()
        with self.assertRaises(
                TypeError,
                msg=("Should be readonly (change assertion"
                     " if class' exception changes type)")):
            od['d'] = -1
        self.assertEqual(len(od), 3, msg="Should still be len 3 since readonly")


if __name__ == "__main__":
    unittest.main()
