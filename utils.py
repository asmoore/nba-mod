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
    search_results = []
    root = test = os.path.dirname(os.path.realpath('__file__'))
    ix = open_dir(root+"/data/")
    with ix.searcher() as searcher:
        query = QueryParser("player_name", ix.schema, termclass=FuzzyTerm).parse(search_input)
        results = searcher.search_page(query,20)
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
        top_links = top_links+'|'+str(counter+1)+' ['+title+'](/r/'+subreddit+'/comments/'+name+')|\n'
    return top_links


def get_schedule(var_length):
    """Return a markdown table of gamges.
    
    """
    #Initiate PRAW
    r = praw.Reddit(user_agent='NBA_MOD using praw')
    #Log in to Reddit using 
    r.login(os.environ['USER'],os.environ['PASS'])
    #Get the schedule from the wiki
    schedule_md = r.get_subreddit('NBA').get_wiki_page('schedule_2014-2015').content_md
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
    r.login(os.environ['USER'],os.environ['PASS'])
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
    r.login(os.environ['USER'],os.environ['PASS'])
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
    
    url = "http://data.nba.com/json/cms/2014/standings/conference.json"
    req = urllib2.urlopen(url).read()
    obs = json.loads(req)

    standings = """|WEST|||EAST|||
|:---:|:---:|:---:|:---:|:---:|:---:|
|**TEAM**|*W/L*|*GB*|**TEAM**|*W/L*|*GB*|
"""

    #for i in range(0,15):
    for i in reversed(range(0,15)):
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
    r.login(os.environ['USER'],os.environ['PASS'])
    success = r.get_subreddit('nba').set_flair(user,flair_text,flair_class)
    return success


if __name__ == '__main__':
    engine = create_engine("postgres://bvbaezxfnrmxev:YYESfSaRGDrxWPrZr8JuAdpoXY@ec2-23-23-188-252.compute-1.amazonaws.com:5432/ddvahv1uqndlvb")
    Session = sessionmaker(bind=engine)    
    session = Session()
    session._model_changes = {}