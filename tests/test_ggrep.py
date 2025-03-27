# -*- coding: utf-8 -*-
import unittest
import sys
import os

TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
# MODULE_DIR = os.path.dirname(MY_DIR)
TEST_DATA_DIR = os.path.join(TESTS_DIR, "data")

REPO_DIR = os.path.dirname(TESTS_DIR)

if __name__ == "__main__":
    sys.path.insert(0, REPO_DIR)

assert os.path.isdir(TEST_DATA_DIR)

from hierosoft import (
    echo0,
    set_verbosity,
)

from hierosoft.ggrep import (
    is_like,
    is_like_any,
    filter_tree,
)

class TestGrepStringMethods(unittest.TestCase):

    def test_is_like(self):
        set_verbosity(True)
        self.assertEqual(is_like("abc", "abc"), True)
        self.assertEqual(is_like("abc", "?bc"), True)
        self.assertEqual(is_like("abc", "a?c"), True)
        self.assertEqual(is_like("abc", "ab?"), True)
        self.assertEqual(is_like("abc", "?b?"), True)
        self.assertEqual(is_like("abc", "???"), True)
        self.assertEqual(is_like("ab", "???"), False)
        self.assertEqual(is_like("abc", "????"), False)
        self.assertEqual(is_like("abc", "??"), False)
        self.assertEqual(is_like("abcd", "???"), False)
        self.assertEqual(is_like("ababab", "ab"), False)
        self.assertEqual(is_like("ab", "ababab"), False)
        self.assertEqual(is_like("a", "aaa"), False)
        self.assertEqual(is_like("aaa", "a"), False)
        self.assertEqual(is_like("ababab", "*ababab"), True)
        self.assertEqual(is_like("ababab", "ababab*"), True)
        self.assertEqual(is_like("abcdab", "*cd*"), True)
        self.assertEqual(is_like("abcdef", "*ef"), True)
        self.assertEqual(is_like("abcdef", "*ab"), False)
        self.assertEqual(is_like("abcdef", "ab*"), True)
        self.assertEqual(is_like("abcdef", "ef*"), False)
        self.assertEqual(is_like("abcdef", "a*f"), True)
        self.assertEqual(is_like("abcdef", "a*f*"), True)
        self.assertEqual(is_like("abcdef", "*a*f"), True)
        self.assertEqual(is_like("abcdef", "*a*f*"), True)
        self.assertEqual(is_like("abcdef", "*b*e*"), True)
        self.assertEqual(is_like("abcdef", "*ab*ef"), True)
        self.assertEqual(is_like("abcdef", "*ab*ef*"), True)
        self.assertEqual(is_like("abcdef", "ab*ef"), True)
        self.assertEqual(is_like("abcdef", "abcde"), False)
        self.assertEqual(is_like("abcdef", "bcdef"), False)
        self.assertEqual(is_like("ababab", "ab"), False)
        self.assertEqual(is_like("/workspace.xml", "/workspace.xml"), True)
        self.assertEqual(is_like("abcdecde", "*cde"), True)
        self.assertEqual(is_like("abcabcde", "abc*"), True)
        self.assertEqual(is_like("/home/foo", "*/foo"), True)
        # As per <https://git-scm.com/docs/gitignore#:~:
        # text=Two%20consecutive%20asterisks%20(%22%20**%20%22,
        # means%20match%20in%20all%20directories.>:
        self.assertEqual(is_like("/home/foo", "**/foo"), True)
        self.assertEqual(is_like("/home/example/foo", "**/foo"), True)
        self.assertEqual(is_like("/home/foo/bar", "**/foo/bar"), True)
        self.assertEqual(is_like("/home/example/foo/bar", "**/foo/bar"), True)
        self.assertEqual(is_like("/home/example/foo/bar", "**/f*o/bar"), True)
        self.assertEqual(
            is_like("/home/example/foo/bar", "/home/**/foo/bar"), True)
        self.assertEqual(
            is_like("/home/examplefoo/bar", "/home/**/foo/bar"), False)
        # self.assertEqual(
        #    is_like("/home/examplefoo/bar", "/home/**foo/bar"), False)
        self.assertEqual(
            is_like("/home/example/foobar", "/home/**/foo/bar"), False)
        # set_verbosity(2)
        self.assertEqual(
            is_like("/home/example/foo/bar", "/home/example/foo/**"), True)
        # set_verbosity(1)
        self.assertEqual(
            is_like("/home/example/foo/bar", "**/bar"), True)
        self.assertEqual(
            is_like("/home/example/foo/bar", "**/bar/bar"), False)

        # As per python gitignore such as in
        # python-lsp-server/.gitignore such as in spyder/external-deps/:
        self.assertEqual(is_like("/home/foo.vscode/", "**/*.vscode/"), True)
        self.assertTrue(
            is_like("Examples/d/foo/example.d", "Examples/d/**/example.d")
        )
        set_verbosity(2)
        self.assertEqual(
            is_like(".gitattributes", "Examples/d/**/example.d"), False)
        # ^ Test for regression regarding issue #22:
        '''
        ValueError: More than one '*' in a row in needle isn't allowed
        (needle="Examples/d/**/example.d"). Outer logic should handle
        special syntax if that is allowed.
        '''
        set_verbosity(1)

        got_the_right_error = False
        try:
            self.assertEqual(is_like("/workspace.xml", None), False)
        except TypeError as ex:
            self.assertTrue(str(ex) in [
                "'NoneType' object is not iterable",
                "'NoneType' object is not subscriptable"
            ])
            got_the_right_error = True
        self.assertEqual(got_the_right_error, True)

        got_the_right_error = False
        try:
            self.assertEqual(is_like(None, "/workspace.xml"), False)
        except TypeError as ex:
            self.assertTrue(str(ex) in [
                "object of type 'NoneType' has no len()",
                "'NoneType' object is not subscriptable"
            ])
            got_the_right_error = True
        self.assertEqual(got_the_right_error, True)

        got_the_right_error = False
        try:
            self.assertEqual(is_like("/workspace.xml", ""), False)
        except ValueError as ex:
            got_the_right_error = True
        self.assertEqual(got_the_right_error, True)

    def test_is_like_any(self):
        set_verbosity(True)

        got_the_right_error = False
        try:
            self.assertEqual(is_like_any("/home/1/abab", None), False)
        except TypeError as ex:
            self.assertEqual(str(ex), "'NoneType' object is not iterable")
            got_the_right_error = True
        self.assertEqual(got_the_right_error, True)

        got_the_right_error = False
        try:
            self.assertEqual(is_like_any(None, "/home/1/abab"), False)
        except TypeError as ex:
            self.assertTrue(str(ex) in [
                "object of type 'NoneType' has no len()",
                "'NoneType' object is not subscriptable"
            ])
            got_the_right_error = True
        self.assertEqual(got_the_right_error, True)

    def test_filter(self):
        test_filter_tree_path = os.path.join(TEST_DATA_DIR, "filter_tree")
        found_not_filtered_file = False
        found_exclusion = True
        exclusion = os.path.join("deep", "deeper", "deepest",
                                 "filter_rel_but_only_dir")
        for path in filter_tree(test_filter_tree_path):
            echo0('* filter_tree yielded "{}"'.format(path))
            assert not path.endswith(".bin")
            if "filtered_only_abs_not_deeper_one" in path:
                only_this_deeper_one_should_be_kept = os.path.join(
                    "deeper",
                    "filtered_only_abs_not_deeper_one",
                )
                echo0('  - only_this_deeper_one_should_be_kept="{}"'
                      ''.format(only_this_deeper_one_should_be_kept))

                self.assertIn(only_this_deeper_one_should_be_kept, path)
                # ^ *substring* in *string* (not a list)
            if "filter_rel_but_only_dir" in path:
                if exclusion in path:
                    found_exclusion = True
                else:
                    assert os.path.isfile(path)
                    found_not_filtered_file = True
        assert found_not_filtered_file
        assert found_exclusion


if __name__ == "__main__":
    unittest.main()