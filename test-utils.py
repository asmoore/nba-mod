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
    #def test_get_team_subreddits(self):
    #	utils.get_team_subreddits(3)


    #def test_get_schedule(self):
    #  	schedule =utils.get_schedule(3)
    #    print schedule
    
    #def test_add_players(self):
    #    utils.add_players()

    #def test_get_players(self):
    #    players = utils.get_players()
    #    print players

    #def test_fetch_search(self):
    #    results = utils.fetch_search("Wade","MIA")
    #    print results

    #def test_add_teams(self):
    #    teams = utils.add_teams()
    
    #def test_get_teams(self):
    #    teams = utils.get_teams()
    #    print teams

    #def test_get_players(self):
    #    players = utils.get_players("MIA")
        #print schedule

    #def test_get_game_threads(self):
    #	utils.get_game_threads()


    #def test_get_standings_nba(self):
    #	standings = utils.get_standings_nba()
    #	print standings

    #def test_update_flair(self):
    #    utils.update_flair("catmoon","[MIA] Hassan Whiteside","Heat1")

    #def test_get_schedule_2(self):
    #    schedule = utils.get_schedule_2(3)
    #    print schedule

    def test_get_playoff_table(self):
        playoff_table = utils.get_playoff_table()
        print playoff_table

if __name__ == '__main__':
    unittest.main()
