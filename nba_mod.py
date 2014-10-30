#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
nba_mod
--------------

main module for nba-mod.

"""
import os
      
import praw

import utils

def create_sidebar():
    """Get the static sidebar elements and callouts to dynamic sidebar
    elements from the /r/NBA wiki. 
    
    """
    #Initiate PRAW
    r = praw.Reddit(user_agent='NBA_MOD using praw')
    #Log in to Reddit using 
    r.login(os.environ['USER'],os.environ['PASS'])
    #Get the sidebar from the wiki
    sidebar_md = r.get_subreddit('NBA').get_wiki_page('edit_sidebar').content_md
    sidebar_md = sidebar_md.replace("&gt;", ">")
    #Split the sidebar by individual lines. Each line is a different game
    sidebar_list = sidebar_md.split('\n')
    sidebar = ""
    for line in sidebar_list:
        if line.startswith("//")==False: 
            if line.startswith("$kill"):
                return "kill"
            elif line.startswith("$team_subreddits"):
                sidebar = sidebar + utils.get_team_subreddits(5)
            elif line.startswith("$schedule"):
                sidebar = sidebar + utils.get_schedule(2)
            elif line.startswith("$game_threads"):
                all_games = utils.get_game_threads()
                sidebar = sidebar + utils.create_scorebar(all_games)
            elif line.startswith("$game_thread_bar"):
                all_games = utils.get_game_threads()
                sidebar = sidebar + utils.create_game_thread_bar(all_games)
            elif line.startswith("$standings"):
                sidebar = sidebar + utils.get_standings_nba()
            else:
                sidebar = sidebar + line

    return sidebar


def update_sidebar(sidebar_text,subreddit):
    """update the sidebar for /r/NBA. 
    
    """
    #Initiate PRAW
    r = praw.Reddit(user_agent='NBA_MOD using praw')
    #Log in to Reddit using 
    r.login(os.environ['USER'],os.environ['PASS'])
    #Get the subreddit's settings
    settings = r.get_subreddit(subreddit).get_settings()
    #Set the description of the sidebar to sidebar_text
    settings['description'] = sidebar_text 
    #Update the settings
    settings = r.get_subreddit(subreddit).update_settings(description=settings['description'])

