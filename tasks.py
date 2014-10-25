#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
tasks
--------------

scheduled tasks.

"""
import nba_mod

def update_nba_sidebar():
    """Task to update the nba sidebar.

    """
    #Create the the sidebar text using nba_mod
    sidebar_text = nba_mod.create_sidebar()
    #Update the sidebar of /r/NBA
    nba_mod.update_sidebar(sidebar_text,'NBA')


#Execute the main function
update_nba_sidebar()

