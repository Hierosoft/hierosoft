# -*- coding: utf-8 -*-
import unittest
import sys
import os

from collections import OrderedDict


my_dir = os.path.dirname(os.path.abspath(__file__))
module_dir = os.path.dirname(my_dir)
repo_dir = os.path.dirname(module_dir)

if __name__ == "__main__":
    sys.path.insert(0, repo_dir)

from hierosoft import moresvg

from hierosoft.moresvg import (  # noqa E402
    SVGSegment,
)

from hierosoft.morelogging import (
    echo0,
    set_verbosity,
    pformat,
)

from hierosoft.morebytes import (
    find_not_quoted,
    without_comments,
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

    def test_str_to_style(self):
        # set_verbosity(2)  # try to uncover infinite loops
        #   such as calling find_not_quoted with wrong start.
        set_verbosity(1)
        expected = OrderedDict(
            color="black",
            padding="0",
        )
        expected['margin-left'] = "1in"
        expected['background-color'] = "rgb(255, 255, 255)"
        style_str_fmt = (
            "  color: %s;"
            "\npadding:%s%s;  "
            "margin-left: %s %s;"
            "background-color: %s %s"
        )
        style_str = (
            style_str_fmt % (
                expected['color'],
                expected['padding'],
                "/*;comment*/",  # This comment is before a key
                "/*comment2 /* */",  # This comment is before a value
                expected['margin-left'],
                expected['background-color'],
                "/* comment3 */",
            )
        )
        expected_no_comments = (
            style_str_fmt % (
                expected['color'],
                expected['padding'],
                "",
                "",
                expected['margin-left'],
                expected['background-color'],
                "",
            )
        )

        # region test find_not_quoted as used in str_to_style
        self.assertEqual(without_comments(style_str), expected_no_comments)
        expected_end = style_str.find(";")
        start = 0
        end = find_not_quoted(style_str, ";", start,
                              quote_mark="'",
                              allow_nested_quotes=False)
        self.assertEqual(end, expected_end)
        value_end = end
        if end < 0:
            value_end = len(style_str)  # keep all if no ender
        # assignment operator index:
        expected_ao_index = style_str.find(":")
        ao_index = find_not_quoted(style_str, ":", start, value_end,
                                   quote_mark="'",
                                   allow_nested_quotes=False)

        self.assertEqual(ao_index, expected_ao_index)
        # endregion

        got = moresvg.str_to_style(style_str)
        if got != expected:
            # This arg won't truncate the dicts like assertEqual does.
            raise AssertionError(
                "\n" + str(pformat(got))
                + "\n!="
                + "\n" + str(pformat(expected))
            )

        self.assertEqual(got, expected)


if __name__ == "__main__":
    testcase = TestMoreSVG()
    count = 0
    for name in dir(testcase):
        if name.startswith("test"):
            count += 1
            fn = getattr(testcase, name)
            fn()  # Look at def test_* for the code if tracebacks start here
    print("%s test(s) passed." % count)