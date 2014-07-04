#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test-nba-mod
--------------

Tests for `nba-mod.nba_mod` module.

"""
import unittest

import nba_mod

class NBAModTest(unittest.TestCase):
    def test_create_sidebar(self):
    	nba_mod.create_sidebar()


    def test_update_sidebar(self):
    	nba_mod.update_sidebar("test","catmoon")


if __name__ == '__main__':
    unittest.main()
