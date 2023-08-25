# -*- coding: utf-8 -*-
import unittest
import sys
import os


my_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(my_dir)
repo_dir = os.path.dirname(module_dir)

if __name__ == "__main__":
    sys.path.insert(0, repo_dir)


from hierosoft.moresvg import (  # noqa E402
    SVGSegment,
)


# MY_DIR = os.path.dirname(os.path.realpath(__file__))
# MODULE_DIR = os.path.dirname(MY_DIR)
# TEST_DATA_DIR = os.path.join(MY_DIR, "data")

# assert os.path.isdir(TEST_DATA_DIR)

class TestMoreSVG(unittest.TestCase):
    """Test only mixed-data (not just string/byte/bytearray) algorithms
    For string/bytes/bytearray functions, see test_morebytes instead
    """
    def test_Path(self):
        segment = SVGSegment()
        segment.buffer = [10, 20, 30, 40, 50, 60]
        #                  0   1   2   3   4   5
        segment.vector_fmt = ["x", "y"]
        self.assertEqual(segment._vector_fmt, ["x", "y"])
        # self.assertEqual(segment._x_i, 0)
        # self.assertEqual(segment._y_i, 1)
        self.assertEqual(len(segment), 3)
        self.assertEqual(segment._2D_to_index(0), 0)
        self.assertEqual(segment._2D_to_index(1), 1)
        self.assertEqual(segment._2D_to_index(2), 2)
        self.assertEqual(segment._2D_to_index(3), 3)
        self.assertEqual(segment.location(0), (10, 20))
        self.assertEqual(segment.location(1), (30, 40))
        self.assertEqual(segment.location(2), (50, 60))
        self.assertEqual(segment.buffer_2d(), [10, 20, 30, 40, 50, 60])

        segment.vector_fmt = ["x", "None", "y"]
        self.assertEqual(segment._vector_fmt, ["x", "None", "y"])
        # self.assertEqual(segment._x_i, 0)
        # self.assertEqual(segment._y_i, 2)
        self.assertEqual(len(segment), 2)
        self.assertEqual(segment._2D_to_index(0), 0)
        self.assertEqual(segment._2D_to_index(1), 2)
        self.assertEqual(segment._2D_to_index(2), 3)
        self.assertEqual(segment._2D_to_index(3), 5)
        self.assertEqual(segment.location(0), (10, 30))
        self.assertEqual(segment.buffer_2d(), [10, 30, 40, 60])

        segment.vector_fmt = ["", "x", "y"]
        self.assertEqual(segment._vector_fmt, ["", "x", "y"])
        # self.assertEqual(segment._x_i, 1)
        # self.assertEqual(segment._y_i, 2)
        self.assertEqual(len(segment), 2)
        self.assertEqual(segment._2D_to_index(0), 1)
        self.assertEqual(segment._2D_to_index(1), 2)
        self.assertEqual(segment._2D_to_index(2), 4)
        self.assertEqual(segment._2D_to_index(3), 5)
        self.assertEqual(segment.location(0), (20, 30))
        self.assertEqual(segment.buffer_2d(), [20, 30, 50, 60])


if __name__ == "__main__":
    testcase = TestMoreSVG()
    count = 0
    for name in dir(testcase):
        if name.startswith("test"):
            count += 1
            fn = getattr(testcase, name)
            fn()  # Look at def test_* for the code if tracebacks start here
    print("%s test(s) passed." % count)