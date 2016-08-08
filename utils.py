#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
utils
--------------

Utility functions for nba-mod.

"""
import datetime
import json
import os
import re
import urllib2
import urllib
from lxml import html
import requests
from operator import itemgetter

import praw
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import OAuth2Util

from whoosh.qparser import QueryParser
from whoosh.query import FuzzyTerm
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.index import open_dir

from models import *


def fetch_search(search_input, team_input):
    """
    Fetch search results.

    """
    east_list = ["TOR", "BOS", "NJN", "PHI", "NYK", "CLE", "CHI", "MIL", "IND", "DET", "ATL", "WAS", "MIA", "CHA", "ORL"]
    west_list = ["POR", "OKC", "UTA", "DEN", "MIN", "GSW", "LAC", "PHO", "SAC", "LAL", "HOU", "MEM", "SAS", "DAL", "NOH"]
    search_results = []
    root = test = os.path.dirname(os.path.realpath('__file__'))
    ix = open_dir(root+"/data/")
    with ix.searcher() as searcher:
        query = QueryParser("player_name", ix.schema, termclass=FuzzyTerm).parse(search_input)
        results = searcher.search_page(query,20)
        if team_input=="NBA":
            for hit in results:
                search_results.append({"team_name":hit["team_name"], "player_name":hit["player_name"]})
        elif team_input=="EAST":
            for hit in results:
                if hit["team_name"] in east_list:
                    search_results.append({"team_name":hit["team_name"], "player_name":hit["player_name"]})
        elif team_input=="WEST":
            for hit in results:
                if hit["team_name"] in west_list:
                    search_results.append({"team_name":hit["team_name"], "player_name":hit["player_name"]})
        else:
            for hit in results:
                if hit["team_name"]==team_input:
                    search_results.append({"team_name":hit["team_name"], "player_name":hit["player_name"]})
    return search_results
    

def add_players():
    team_list = ['ATL', 'BOS', 'NJN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW',
                 'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NOH', 'NYK',
                 'OKC', 'ORL', 'PHI', 'PHO', 'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS']
    root = test = os.path.dirname(os.path.realpath('__file__'))
    schema = Schema(player_name=TEXT(stored=True), 
                    team_name=TEXT(stored=True))
    ix = create_in(root+"/data/", schema)
    writer = ix.writer()
    for team in team_list:
        url = 'http://www.basketball-reference.com/teams/' + team + '/players.html'
        page = requests.get(url)
        tree = html.fromstring(page.text)
        players = tree.xpath('//tr/td/a/text()')
        for player in players:
            writer.add_document(player_name=unicode(player), team_name=unicode(team))
    writer.commit()


def get_players():
    games = db.session.query(Player)
    return games


def get_team_subreddits(var_length):
    """Return a markdown table of top team subreddit threads.
        
    """
    #Define the URL with var_length number of posts.
    url = "http://www.reddit.com/r/nyknicks+sixers+bostonceltics+gonets+torontoraptors+chicagobulls+mkebucks+clevelandcavs+indianapacers+detroitpistons+heat+atlantahawks+orlandomagic+charlottehornets+washingtonwizards+timberwolves+thunder+ripcity+utahjazz+denvernuggets+warriors+laclippers+kings+suns+lakers+nbaspurs+mavericks+memphisgrizzlies+rockets+hornets/.json?limit=" + str(var_length)
    #Define headers for Reddit API request.
    headers = { 'User-Agent' : '/r/nba subreddits /u/NBA_Mod' }
    #Request the URL.
    req = urllib2.Request(url, None, headers)
    #Open the URL.
    c = urllib2.urlopen(req).read()
    #Load the JSON data from Reddit
    obs = json.loads(c)
    #start the top_links string
    top_links = '\n\n|Top Team Subreddit Posts|\n|:---|\n'
    #link_by_ID = 'http://www.reddit.com/r/nba/by_id/'
    for (counter, story) in enumerate(obs['data']['children']):
        title = story['data']['title']
        name = story['data']['name']
        exclusion_list = ['(', ')', ']', '[', '\n', '|', '/']
        for exclusion in exclusion_list:
            title = title.replace(exclusion,'')
        name = name.replace('t3_', '')
        subreddit = story['data']['subreddit'].lower()
        permalink = story['data']['permalink']
        top_links = top_links+'|'+str(counter+1)+' ['+title+'](https://np.reddit.com/r/'+subreddit+'/comments/'+name+')|\n'
    return top_links


def get_schedule(var_length):
    """Return a markdown table of gamges.
    
    """
    #Initiate PRAW
    r = praw.Reddit(user_agent='/u/NBA_MOD for /r/NBA')
    #Log in to Reddit using 
    
    o = OAuth2Util.OAuth2Util(r, print_log=True, configfile="conf.ini")
    #r.login(os.environ['USER'],os.environ['PASS'])
    

    #Get the schedule from the wiki
    schedule_md = r.get_subreddit('NBA').get_wiki_page('schedule_2015-2016').content_md
    #Split the schedule by individual lines. Each line is a different game
    games = schedule_md.split('\n')
    #Add the header to the schedule table 
    schedule = "|Date|Away|Home|Time (ET)|Nat TV|\n|:---|:---|:---|:---|:---|\n"
    #Loop through each game
    for game in games:
        #Get the date of the game
        date = re.search("(\d+/\d+/\d+)",game)
        #This is necessary to skip some of the header lines from the wiki table
        if date != None:
            #Find out how many days there are between the game and today
            intElapsed = int((datetime.datetime.strptime(str(date.group()),'%m/%d/%Y').date() - datetime.datetime.today().date()).days)
            ##intElapsed = int((datetime.datetime.strptime(str(date.group()),'%m/%d/%Y').date() - datetime.datetime.strptime('10/29/2013','%m/%d/%Y').date()).days)
            #Only populate the table with games between today and three days from now
            if intElapsed >= 0 and intElapsed <= var_length:
                #If the schedule already has a game that day remove the date
                #Either way add the game to the schedule with a new line
                if re.search(datetime.datetime.strptime(date.group(), '%m/%d/%Y').strftime('%b. %d'), schedule):
                    schedule = schedule + re.sub(date.group(),"",game) + "\n"
                else:
                    schedule = schedule + re.sub(date.group(),datetime.datetime.strptime(date.group(), '%m/%d/%Y').strftime('%b. %d'),game) + "\n"
    #Returns as a string
    return schedule

def get_schedule_nba():
    """Gets the schedule from nba.com

    """
    response = urllib2.urlopen('http://data.nba.com/5s/json/cms/noseason/scoreboard/'+datetime.now(pytz.timezone('US/Pacific')).strftime("%Y%m%d")+'/games.json')
    jdata = json.load(response)
    games = jdata['sports_content']['games']['game']
    schedule = []
    time = str(datetime.now())
    for game in games:
        home=game['home']['city']
        visitor=game['visitor']['city']
        game_id=game['id']
        date=game['home_start_date']
        date_obj = datetime.strptime(date, "%Y%m%d")
        date_formatted = date_obj.strftime("%b. %d, %Y")
        title = "GAME THREAD: " + visitor + " @ " + home + " - (" + date_formatted + ")"
        schedule.append(Game(date,game_id,home,visitor,title))

    return schedule

def get_game_threads():
    """Return a string list of current games.
    
    """
    #Open score URL on ESPN
    url = 'http://sports.espn.go.com/nba/bottomline/scores'
    #Read the URL
    scores = urllib.urlopen(url).read()
    #Format the URL text.
    scores = re.sub("%20%20"," @",scores)
    scores = re.sub("%20"," ",scores)
    scores = re.sub("%26","",scores)
    scores = re.sub("\^", "",scores)
    scores = re.sub(" at ", " @ ",scores)
    scores = re.sub("[0-9]=","",scores)
    scores = re.sub("&nba_s_right([0-9])_count=[0-9][0-9]&","",scores)
    scores = re.sub("&","",scores)
    #Split the formatted scores into individual games
    all_games = re.split('nba_s_left',scores)

    return all_games

def create_scorebar(all_games):
    #Create scorebar
    scorebar = "||||||\n|:--|:--|:--|:--|:--|:--|\n|Game Threads|"
    #Initialize lists
    list_scorebar = [];
    list_pattern = [];
    #Go through each game
    for game in all_games:
        #If "@" isn't in the game then this is extra info on ESPN
        if re.search("@", game):
            #Format game to create a REGEX pattern to search /r/NBA threads with
            game_formatted = re.split("nba",game)[0]
            game_formatted = game_formatted.lstrip('1')
            list_scorebar.append(game_formatted.replace("(","[("))
            game_formatted = re.sub("\\(.+?\\)","",game_formatted)
            game_formatted = re.sub("[0-9]","",game_formatted)
            game_formatted = re.sub(" @ ", ".*", game_formatted)
            game_formatted = re.sub(" \.\*", ".*", game_formatted)
            game_formatted = game_formatted.rstrip()
            game_formatted = game_formatted.replace("LA Clippers","Los Angeles Clippers")
            game_formatted = game_formatted.replace("LA Lakers","Los Angeles Lakers")
            #add to list_pattern
            list_pattern.append(game_formatted)
    #Initialize PRAW
    r = praw.Reddit(user_agent='NBA_MOD using praw')
    #Login using the NBAModBot password
    #r.login(os.environ['USER'],os.environ['PASS'])
    o = OAuth2Util.OAuth2Util(r, print_log=True, configfile="conf.ini")
    #Get top 100 submissions from /r/NBA. In high traffic this may need to be increased.
    submissions = r.get_subreddit('nba').get_hot(limit=100)
    #Create lists
    game_thread_title = [];
    game_thread_link = [];
            
    for submission in submissions:
        story = submission.title.encode("utf8")
        link = submission.permalink
        if re.search('GAME THREAD',str(story),re.IGNORECASE):
            game_thread_title.append(str(story))
            temp_game_thread = re.search('/r/nba/comments/[0-9A-Za-z][0-9A-Za-z][0-9A-Za-z][0-9A-Za-z][0-9A-Za-z][0-9A-Za-z]/',submission.permalink)
            game_thread_link.append(str(temp_game_thread.group()))
            
    for i in range(0, len(list_pattern)):
        temp = '* ' + list_scorebar[i] + '\n';
        for j in range(0, len(game_thread_title)):
            if re.search(list_pattern[i], game_thread_title[j]):
                temp = '* ' + list_scorebar[i]+']('+game_thread_link[j].replace('/r/nba/comments','')+')|'
        scorebar = scorebar + temp
    #Replace the city names with hrefs (e.g. "Miami" to "[](/MIA)")
    scorebar = city_names_to_subs(scorebar)
    #Add markdown
    scorebar = scorebar + "-|[**GAME THREAD GENERATOR**](http://nba-gamethread.herokuapp.com/)|\n\n"
    
    return scorebar


def create_game_thread_bar(all_games):
    """Return a string list of current games.
    
    """
    #Create scorebar
    scorebar = ""
    #Initialize lists
    list_scorebar = [];
    list_pattern = [];
    #Go through each game
    for game in all_games:
        #If "@" isn't in the game then this is extra info on ESPN
        if re.search("@", game):
            #Format game to create a REGEX pattern to search /r/NBA threads with
            game_formatted = re.split("nba",game)[0]
            game_formatted = game_formatted.lstrip('1')
            game_formatted1 = game_formatted.replace("[", "")
            game_formatted1 = game_formatted1.replace(")", "")
            game_formatted1 = game_formatted1.replace(" ET", "")
            list_scorebar.append(game_formatted1)
            game_formatted = re.sub("\\(.+?\\)","",game_formatted)
            game_formatted = re.sub("[0-9]","",game_formatted)
            game_formatted = re.sub(" @ ", ".*", game_formatted)
            game_formatted = re.sub(" \.\*", ".*", game_formatted)
            game_formatted = game_formatted.rstrip()
            game_formatted = game_formatted.replace("LA Clippers","Los Angeles Clippers")
            game_formatted = game_formatted.replace("LA Lakers","Los Angeles Lakers")
            #add to list_pattern
            list_pattern.append(game_formatted)
    #Initialize PRAW
    r = praw.Reddit(user_agent='NBA_MOD using praw')
    #Login using the NBAModBot password
    #r.login(os.environ['USER'],os.environ['PASS'])
    o = OAuth2Util.OAuth2Util(r, print_log=True, configfile="conf.ini")
    #Get top 100 submissions from /r/NBA. In high traffic this may need to be increased.
    submissions = r.get_subreddit('nba').get_hot(limit=100)
    #Create lists
    game_thread_title = [];
    game_thread_link = [];
            
    for submission in submissions:
        story = submission.title.encode("utf8")
        link = submission.permalink
        if re.search('GAME THREAD',str(story),re.IGNORECASE):
            game_thread_title.append(str(story))
            temp_game_thread = re.search('/r/nba/comments/[0-9A-Za-z][0-9A-Za-z][0-9A-Za-z][0-9A-Za-z][0-9A-Za-z][0-9A-Za-z]/',submission.permalink)
            game_thread_link.append(str(temp_game_thread.group()))
            
    for i in range(0, len(list_pattern)):
        temp = '> * ' + list_scorebar[i] + '\n'
        temp = temp.replace("(", "")
        for j in range(0, len(game_thread_title)):
            if re.search(list_pattern[i], game_thread_title[j]):
                temp = '> * ' + list_scorebar[i]+']('+game_thread_link[j].replace('/r/nba/comments','')+')'+'\n'
                temp = temp.replace(" (", " [")
        temp = temp.replace(" @ ", " ")
        temp = temp.replace(" - ", "-")
        temp = temp.replace(" IN ", " ")
        scorebar = scorebar + temp
    #Replace the city names with hrefs (e.g. "Miami" to "[](/MIA)")
    scorebar = city_names_to_code(scorebar)

    return scorebar


def get_standings_nba():
    """Get standings from data.nba.com """
    
    url = "http://data.nba.com/json/cms/2015/standings/conference.json"
    req = urllib2.urlopen(url).read()
    obs = json.loads(req)

    standings = """|WEST|||EAST|||
|:---:|:---:|:---:|:---:|:---:|:---:|
|**TEAM**|*W/L*|*GB*|**TEAM**|*W/L*|*GB*|
"""

    for i in range(0,15):
    #for i in reversed(range(0,15)):
        east = obs["sports_content"]["standings"]["conferences"]["East"]["team"][i]
        east_name = east["abbreviation"]
        east_record = east["team_stats"]["wins"] + "-" + east["team_stats"]["losses"]
        east_gb_conf = east["team_stats"]["gb_conf"]
        west = obs["sports_content"]["standings"]["conferences"]["West"]["team"][i]
        west_name = west["abbreviation"]
        west_record = west["team_stats"]["wins"] + "-" + west["team_stats"]["losses"]
        west_gb_conf = west["team_stats"]["gb_conf"]
        east_div_rank = east["team_stats"]["div_rank"]
        west_div_rank = west["team_stats"]["div_rank"]
        east_rank = str(i+1)
        west_rank = str(i+1)
        if east_div_rank == "1":
            east_rank = "\* "+ east_rank
        if west_div_rank == "1":
            west_rank = "\* "+ west_rank
        if i < 8:
            standings = standings + "|" + west_rank + " [](/" + west_name + ")| " + west_record + " | " + west_gb_conf + "|" + east_rank + " [](/" + east_name + ")| " + east_record + " | " + east_gb_conf + " |\n"

        else:
            standings = standings + "|[](/" + west_name + ")| " + west_record + " | " + west_gb_conf + " |[](/" + east_name + ")| " + east_record + " | " + east_gb_conf + " |\n"
            
    return standings



def city_names_to_hrefs(var_string):
    """Replace city names in a string with team hrefs.
    
    """
    #Use the input variable to be modified
    city_names_to_hrefs = var_string

    #List of NBA city names
    city_names = ['Boston','Brooklyn','New York','Philadelphia','Toronto',
                  'Chicago','Cleveland','Detroit','Indiana','Milwaukee',
                  'Atlanta','Charlotte','Miami','Orlando','Washington',
                  'Golden State','Golden St','LA Clippers','LA Lakers','Los Angeles Clippers',
                  'Los Angeles Lakers','Phoenix','Sacramento','Dallas','Houston',
                  'Memphis','New Orleans','San Antonio','Denver','Minnesota',
                  'Oklahoma City','Portland','Philadelphia','Utah'
                  ]
    #Corresponding list of hrefs
    hrefs = ['[](/BOS)','[](/BKN)','[](/NYK)','[](/PHI)','[](/TOR)',
             '[](/CHI)','[](/CLE)','[](/DET)','[](/IND)','[](/MIL)',
             '[](/ATL)','[](/CHA)','[](/MIA)','[](/ORL)','[](/WAS)',
             '[](/GSW)','[](/GSW)','[](/LAC)','[](/LAL)','[](/LAC)',
             '[](/LAL)','[](/PHX)','[](/SAC)','[](/DAL)','[](/HOU)',
             '[](/MEM)','[](/NOP)','[](/SAS)','[](/DEN)','[](/MIN)',
             '[](/OKC)','[](/POR)','[](/PHI)','[](/UTA)'
             ]
    #Go through the lists
    for city,href in zip(city_names,hrefs):
        #Replace all of the city names with hrefs
        city_names_to_hrefs = city_names_to_hrefs.replace(city,href)
    return city_names_to_hrefs


def city_names_to_code(var_string):
    """Replace city names in a string with team hrefs.
    
    """
    #Use the input variable to be modified
    city_names_to_hrefs = var_string

    #List of NBA city names
    city_names = ['Boston','Brooklyn','New York','Philadelphia','Toronto',
                  'Chicago','Cleveland','Detroit','Indiana','Milwaukee',
                  'Atlanta','Charlotte','Miami','Orlando','Washington',
                  'Golden State','Golden St','LA Clippers','LA Lakers','Los Angeles Clippers',
                  'Los Angeles Lakers','Phoenix','Sacramento','Dallas','Houston',
                  'Memphis','New Orleans','San Antonio','Denver','Minnesota',
                  'Oklahoma City','Portland','Philadelphia','Utah'
                  ]
    #Corresponding list of hrefs
    hrefs = ['**BOS**','**BKN**','**NYK**','**PHI**','**TOR**',
             '**CHI**','**CLE**','**DET**','**IND**','**MIL**',
             '**ATL**','**CHA**','**MIA**','**ORL**','**WAS**',
             '**GSW**','**GSW**','**LAC**','**LAL**','**LAC**',
             '**LAL**','**PHX**','**SAC**','**DAL**','**HOU**',
             '**MEM**','**NOP**','**SAS**','**DEN**','**MIN**',
             '**OKC**','**POR**','**PHI**','**UTA**'
             ]
    #Go through the lists
    for city,href in zip(city_names,hrefs):
        #Replace all of the city names with hrefs
        city_names_to_hrefs = city_names_to_hrefs.replace(city,href)
    return city_names_to_hrefs


def city_names_to_subs(var_string):
    """Replace city names in a string with team subreddits.
    
    """
    #Use the input variable to be modified
    city_names_to_subs = var_string

    #List of NBA city names
    city_names = ['Boston','Brooklyn','New York','Philadelphia','Toronto',
                  'Chicago','Cleveland','Detroit','Indiana','Milwaukee',
                  'Atlanta','Charlotte','Miami','Orlando','Washington',
                  'Golden State','Golden St','LA Clippers','LA Lakers','Los Angeles Clippers',
                  'Los Angeles Lakers','Phoenix','Sacramento','Dallas','Houston',
                  'Memphis','New Orleans','San Antonio','Denver','Minnesota',
                  'Oklahoma City','Portland','Philadelphia','Utah'
                  ]
    #Corresponding list of subs
    subs = ['bostonceltics','gonets','nyknicks','sixers','torontoraptors',
             'chicagobulls','clevelandcavs','detroitpistons','indianapacers','mkebucks',
             'atlantahawks','charlottehornets','heat','orlandomagic','washingtonwizards',
             'warriors','warriors','laclippers','lakers','laclippers',
             'lakers','suns','kings','mavericks','rockets',
             'memphisgrizzlies','nolapelicans','nbaspurs','denvernuggets','timberwolves',
             'thunder','ripcity','sixers','utahjazz'
             ]
    #Go through the lists
    for city,sub in zip(city_names,subs):
        #Replace all of the city names with hrefs
        href = "[](/r/"+sub+")"
        city_names_to_subs = city_names_to_subs.replace(city,href)
    return city_names_to_subs


def update_flair(user,flair_text,flair_class):
    """Update a user's flair

    """
    r = praw.Reddit(user_agent='NBA_MOD using praw')
    #r.login(os.environ['USER'],os.environ['PASS'])
    o = OAuth2Util.OAuth2Util(r, print_log=True, configfile="conf.ini")
    success = r.get_subreddit('nba').set_flair(user,flair_text,flair_class)
    return success


def get_team_from_flair_class(css):
    team_flair_list = [{"flair_name":"EAST","team":"Other"},
                    {"flair_name":"WEST","team":"Other"},
                    {"flair_name":"NBA","team":"Other"},
                    {"flair_name":"76ers1","team":"Philadelphia"},
                    {"flair_name":"76ers3","team":"Philadelphia"},
                    {"flair_name":"76ers2","team":"Philadelphia"},
                    {"flair_name":"Bobcats1","team":"Charlotte"},
                    {"flair_name":"Bobcats2","team":"Charlotte"},
                    {"flair_name":"Bobcats3","team":"Charlotte"},
                    {"flair_name":"Bobcats4","team":"Charlotte"},
                    {"flair_name":"Braves","team":"Other"},
                    {"flair_name":"Bucks1","team":"Milwaukee"},
                    {"flair_name":"Bucks2","team":"Milwaukee"},
                    {"flair_name":"Bucks3","team":"Milwaukee"},
                    {"flair_name":"Bucks4","team":"Milwaukee"},
                    {"flair_name":"Bullets","team":"Washington"},
                    {"flair_name":"Bulls","team":"Chicago"},
                    {"flair_name":"Cavaliers1","team":"Cleveland"},
                    {"flair_name":"Cavaliers2","team":"Cleveland"},
                    {"flair_name":"Cavaliers3","team":"Cleveland"},
                    {"flair_name":"Celtics1","team":"Boston"},
                    {"flair_name":"Celtics2","team":"Boston"},
                    {"flair_name":"Clippers","team":"L.A. Clippers"},
                    {"flair_name":"Clippers2","team":"L.A. Clippers"},
                    {"flair_name":"Clippers3","team":"L.A. Clippers"},
                    {"flair_name":"Generals","team":"Other"},
                    {"flair_name":"Grizzlies","team":"Memphis"},
                    {"flair_name":"Grizzlies2","team":"Memphis"},
                    {"flair_name":"Hawks1","team":"Atlanta"},
                    {"flair_name":"Hawks2","team":"Atlanta"},
                    {"flair_name":"Hawks3","team":"Atlanta"},
                    {"flair_name":"Heat","team":"Miami"},
                    {"flair_name":"Heat2","team":"Miami"},
                    {"flair_name":"Heat3","team":"Miami"},
                    {"flair_name":"Hornets","team":"Charlotte"},
                    {"flair_name":"OKCHornets","team":"Oklahoma City"},
                    {"flair_name":"Pelicans","team":"New Orleans"},
                    {"flair_name":"Pelicans2","team":"New Orleans"},
                    {"flair_name":"Pelicans3","team":"New Orleans"},
                    {"flair_name":"Pelicans4","team":"New Orleans"},
                    {"flair_name":"Pelicans5","team":"New Orleans"},
                    {"flair_name":"Jazz1","team":"Utah"},
                    {"flair_name":"Jazz2","team":"Utah"},
                    {"flair_name":"Jazz3","team":"Utah"},
                    {"flair_name":"Jazz4","team":"Utah"},
                    {"flair_name":"Jazz5","team":"Utah"},
                    {"flair_name":"Kings1","team":"Sacramento"},
                    {"flair_name":"Kings2","team":"Sacramento"},
                    {"flair_name":"Kings3","team":"Sacramento"},
                    {"flair_name":"Knicks1","team":"New York"},
                    {"flair_name":"Knicks2","team":"New York"},
                    {"flair_name":"Knicks3","team":"New York"},
                    {"flair_name":"Knicks4","team":"New York"},
                    {"flair_name":"Knicks5","team":"New York"},
                    {"flair_name":"KnickerBockers","team":"New York"},
                    {"flair_name":"Lakers1","team":"L.A. Lakers"},
                    {"flair_name":"Lakers2","team":"L.A. Lakers"},
                    {"flair_name":"Lakers3","team":"L.A. Lakers"},
                    {"flair_name":"MinnLakers","team":"Minnesota"},
                    {"flair_name":"Magic1","team":"Orlando"},
                    {"flair_name":"Magic2","team":"Orlando"},
                    {"flair_name":"Magic3","team":"Orlando"},
                    {"flair_name":"Magic4","team":"Orlando"},
                    {"flair_name":"Mavs1","team":"Dallas"},
                    {"flair_name":"Mavs2","team":"Dallas"},
                    {"flair_name":"Mavs3","team":"Dallas"},
                    {"flair_name":"Nets1","team":"Brooklyn"},
                    {"flair_name":"Nets2","team":"Brooklyn"},
                    {"flair_name":"Nets3","team":"Brooklyn"},
                    {"flair_name":"Nuggets1","team":"Denver"},
                    {"flair_name":"Nuggets2","team":"Denver"},
                    {"flair_name":"Nuggets3","team":"Denver"},
                    {"flair_name":"Nuggets4","team":"Denver"},
                    {"flair_name":"Pacers1","team":"Indiana"},
                    {"flair_name":"Pacers2","team":"Indiana"},
                    {"flair_name":"Pistons1","team":"Detroit"},
                    {"flair_name":"Pistons2","team":"Detroit"},
                    {"flair_name":"Pistons3","team":"Detroit"},
                    {"flair_name":"Pistons4","team":"Detroit"},
                    {"flair_name":"Raptors1","team":"Toronto"},
                    {"flair_name":"Raptors2","team":"Toronto"},
                    {"flair_name":"Raptors3","team":"Toronto"},
                    {"flair_name":"Raptors4","team":"Toronto"},
                    {"flair_name":"Raptors5","team":"Toronto"},
                    {"flair_name":"Raptors6","team":"Toronto"},
                    {"flair_name":"Raptors7","team":"Toronto"},
                    {"flair_name":"TorHuskies","team":"Toronto"},
                    {"flair_name":"Rockets1","team":"Houston"},
                    {"flair_name":"Rockets2","team":"Houston"},
                    {"flair_name":"Rockets3","team":"Houston"},
                    {"flair_name":"Spurs1","team":"San Antonio"},
                    {"flair_name":"Spurs2","team":"San Antonio"},
                    {"flair_name":"Spurs3","team":"San Antonio"},
                    {"flair_name":"Suns1","team":"Phoenix"},
                    {"flair_name":"Suns2","team":"Phoenix"},
                    {"flair_name":"Suns3","team":"Phoenix"},
                    {"flair_name":"Suns4","team":"Phoenix"},
                    {"flair_name":"Suns5","team":"Phoenix"},
                    {"flair_name":"Suns6","team":"Phoenix"},
                    {"flair_name":"Supersonics1","team":"Seattle"},
                    {"flair_name":"Supersonics2","team":"Seattle"},
                    {"flair_name":"Thunder","team":"Oklahoma City"},
                    {"flair_name":"Timberwolves1","team":"Minnesota"},
                    {"flair_name":"Timberwolves2","team":"Minnesota"},
                    {"flair_name":"Timberwolves3","team":"Minnesota"},
                    {"flair_name":"Timberwolves4","team":"Minnesota"},
                    {"flair_name":"TrailBlazers1","team":"Portland"},
                    {"flair_name":"TrailBlazers2","team":"Portland"},
                    {"flair_name":"TrailBlazers3","team":"Portland"},
                    {"flair_name":"TrailBlazers4","team":"Portland"},
                    {"flair_name":"TrailBlazers5","team":"Portland"},
                    {"flair_name":"Warriors1","team":"Golden State"},
                    {"flair_name":"Warriors2","team":"Golden State"},
                    {"flair_name":"Warriors3","team":"Golden State"},
                    {"flair_name":"Wizards","team":"Washington"},
                    {"flair_name":"Wizards2","team":"Washington"},
                    {"flair_name":"Wizards3","team":"Washington"},
                    {"flair_name":"Wizards4","team":"Washington"},
                    {"flair_name":"Wizards5","team":"Washington"},
                    {"flair_name":"ChaHornets","team":"Charlotte"},
                    {"flair_name":"ChaHornets2","team":"Charlotte"},
                    {"flair_name":"ChaHornets3","team":"Charlotte"},
                    {"flair_name":"ChaHornets4","team":"Charlotte"},
                    {"flair_name":"ChaHornets5","team":"Charlotte"},
                    {"flair_name":"ChaHornets6","team":"Charlotte"},
                    {"flair_name":"VanGrizzlies","team":"Memphis"},
                    {"flair_name":"VanGrizzlies2","team":"Memphis"},
                    {"flair_name":"VanGrizzlies3","team":"Memphis"}]
    team_name = ""
    for team in team_flair_list:
        if css == team["flair_name"]:
            team_name = team["team"]
    if len(team) == 0:
        team_name = "Other"
    return team_name


def get_flair_count():

    r = praw.Reddit('/u/catmoon using praw')
    #r.login(os.environ['USER'],os.environ['PASS'])
    o = OAuth2Util.OAuth2Util(r, print_log=True, configfile="conf.ini")
    subreddit = r.get_subreddit('nba')
    flairlist = subreddit.get_flair_list(limit=None)
    flair_count = []
    
    for flair in flairlist:
         css = flair['flair_css_class']
         #flair_text = flair['flair_text
         match = False
         for index, counted_flair in enumerate(flair_count):
            if counted_flair["flairname"] == css:
                counted_flair["number"] = counted_flair["number"] + 1
                match = True
         if match == False:
             flair_count.append({'flairname':css, 'number':1,'team':get_team_from_flair_class(css)})
    #     print flair_count
    #flair_count = [{'color': 'rgba(159,234,231)', 'number': 1, 'flairname': u'Nets3', 'team': 'Chicago'}, {'color': 'rgba(144,84,240)', 'nu-mber': 1, 'flairname': u'Raptors1', 'team': 'Chicago'}, {'color': 'rgba(247,20,222)', 'number': 1, 'flairname': u'Rockets1', 'team': 'Chicago'}]
    return flair_count


def update_flair_list():
    flair_list = get_flair_count()
    flair_json = json.dumps([dict(jflair=lflair) for lflair in flair_list])
    flair = Flair(jsondata=json.dumps(flair_json), date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    db.session.add(flair)
    db.session.commit()


if __name__ == '__main__':
    engine = create_engine(os.environ['DATABASE_URL'])
    Session = sessionmaker(bind=engine)    
    session = Session()
    session._model_changes = {}
    add_players()
