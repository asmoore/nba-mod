#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test-utils
--------------

Tests for `nba-mod.utils` module.

"""
import unittest

import utils

class UtilsTest(unittest.TestCase):
    def test_get_team_subreddits(self):
    	utils.get_team_subreddits(3)


    def test_get_schedule(self):
    	utils.get_schedule(3)
    

    def test_get_game_threads(self):
    	utils.get_game_threads()


    def test_get_standings(self):
    	utils.get_standings()


if __name__ == '__main__':
    unittest.main()