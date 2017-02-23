#!/bin/env python3
# -*- coding: utf-8 -*-

"""
Test the 'utils.py' code.
"""

import sys
import os
import getopt
sys.path.append('..')
import utils

import unittest


class TestUtils(unittest.TestCase):
    def test_make_multiple(self):
        """A simple test for the make_multiple() function."""

        # easy smoke test
        given = 4.3
        multiple = 5
        expected = 5
        actual = utils.make_multiple(given, multiple)
        msg = ('Given %s, using multiple %s, expected %s, got %s'
               % (str(given), str(multiple), str(expected), str(actual)))
        self.assertEqual(actual, expected, msg)

        # just below and very close to a multiple
        given = 9.99
        multiple = 5
        expected = 10
        actual = utils.make_multiple(given, multiple)
        msg = ('Given %s, using multiple %s, expected %s, got %s'
               % (str(given), str(multiple), str(expected), str(actual)))
        self.assertEqual(actual, expected, msg)

        # just above and very close to a multiple
        given = 15.001
        multiple = 5
        expected = 15
        actual = utils.make_multiple(given, multiple)
        msg = ('Given %s, using multiple %s, expected %s, got %s'
               % (str(given), str(multiple), str(expected), str(actual)))
        self.assertEqual(actual, expected, msg)

        # just above midway between two multiples
        given = 12.5001
        multiple = 5
        expected = 15
        actual = utils.make_multiple(given, multiple)
        msg = ('Given %s, using multiple %s, expected %s, got %s'
               % (str(given), str(multiple), str(expected), str(actual)))
        self.assertEqual(actual, expected, msg)

        # just below midway between two multiples
        given = 12.499
        multiple = 5
        expected = 10
        actual = utils.make_multiple(given, multiple)
        msg = ('Given %s, using multiple %s, expected %s, got %s'
               % (str(given), str(multiple), str(expected), str(actual)))
        self.assertEqual(actual, expected, msg)


unittest.main()
