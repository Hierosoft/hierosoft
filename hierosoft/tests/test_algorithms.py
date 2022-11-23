# -*- coding: utf-8 -*-
import unittest
import sys
import os

from hierosoft import (
    echo0,
    set_verbosity,
    find_by_value,
)


# MY_DIR = os.path.dirname(os.path.realpath(__file__))
# MODULE_DIR = os.path.dirname(MY_DIR)
# TEST_DATA_DIR = os.path.join(MY_DIR, "data")

# assert os.path.isdir(TEST_DATA_DIR)

class TestAlgorithms(unittest.TestCase):

    def test_find_by_value(self):
        l = [
            {
                'name': 'Bo',
                'id': 100
            },
            {
                'name': 'Jo',
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



