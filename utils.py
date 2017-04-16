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
from lxml import html, etree
import requests
from operator import itemgetter
#from datetime import datetime
import pytz

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
        #players = tree.xpath('//tr/td/a/text()')
        #for player in players:
        #    to = players.xpath('//tr/td[4]/text()') 
        #    print "To: " + str(to)
        team_name = team
        players = tree.xpath('//tr')
        for player in players:
            column = player.getchildren() 
            name = column[1].text_content()
            fro = column[2].text_content()
            to = column[3].text_content()
            if name == "Player" or to == "Per Game":
                pass
            else:
                if team == "OKC":
                    if int(to) < int(2008):
                        team_name = "SEA"
                    elif int(fro) < int(2009):
                        writer.add_document(player_name=unicode(str(name)), team_name=unicode(str("SEA")))
                        team_name = "OKC"
                    else:
                        team_name = "OKC"
                else:
                    pass
                writer.add_document(player_name=unicode(str(name)), team_name=unicode(str(team_name)))
    writer.commit()


def get_players():
    games = db.session.query(Player)
    return games


def get_team_subreddits(var_length):
    """Return a markdown table of top team subreddit threads.
        
    """
    #Define the URL with var_length number of posts.
    url = "http://www.reddit.com/r/nyknicks+sixers+bostonceltics+gonets+torontoraptors+chicagobulls+mkebucks+clevelandcavs+pacers+detroitpistons+heat+atlantahawks+orlandomagic+charlottehornets+washingtonwizards+timberwolves+thunder+ripcity+utahjazz+denvernuggets+laclippers+kings+suns+lakers+nbaspurs+mavericks+memphisgrizzlies+rockets+hornets/.json?limit=" + str(var_length)
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

def get_schedule_2(var_length):
    """Return a markdown table of games.
    
    """
    schedule = "|Date|Away|Home|Time (ET)|Nat TV|\n|:---|:---|:---|:---|:---|\n"
    today = datetime.datetime.now(pytz.timezone('US/Pacific'))
    for i in range(0,var_length):
        first_for_day = True
        date = today + datetime.timedelta(days=i)
        url_date = 'http://data.nba.com/5s/json/cms/noseason/scoreboard/'+date.strftime("%Y%m%d")+'/games.json'
        try:
            response = urllib2.urlopen(url_date)
        
            jdata = json.load(response)
            games = jdata['sports_content']['games']['game']
            for game in games:
                away = game['visitor']['abbreviation']
                home = game['home']['abbreviation']
                time24 = game['time']
                time = datetime.time(hour=int(time24[0:2]), minute=int(time24[2:4])).strftime('%I:%M %p')
                broadcaster = "[](/" + game['broadcasters']['tv']['broadcaster'][0]['display_name'] + ")"
                if first_for_day:
                    line = "|" + date.strftime('%b. %d') + "|[](/" + away + ")|[](/" + home + ")|" + time + "|" + broadcaster + "\n"
                else:
                    line = "| |[](/" + away + ")|[](/" + home + ")|" + time + "|" + broadcaster + "\n"
                schedule = schedule + line
                first_for_day = False
        except IOError, e:
            print "no games that day"
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


def get_playoff_table():
    """Return playoff from ESPN

    """
    playoff_table = "|RD1|RD2|WCF|FIN|ECF|RD2|RD1|\n|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n"

    url = "http://www.espn.com/nba/bracket"
    page = requests.get(url)
    tree = html.fromstring(page.text)
    bracket_table = tree.xpath('//*[@id="my-teams-table"]/div[1]/div/div')
    round_1 = tree.xpath('//*[@id="my-teams-table"]/div[1]/div/div[4]/dl/dt')
    round_2 = tree.xpath('//*[@id="my-teams-table"]/div[1]/div/div[5]/dl/dt')
    round_3 = tree.xpath('//*[@id="my-teams-table"]/div[1]/div/div[6]/dl/dt')
    round_4 = tree.xpath('//*[@id="my-teams-table"]/div[1]/div/div[7]/dl/dt')
    round_1_series = tree.xpath('//*[@id="my-teams-table"]/div[1]/div/div[4]/dl/dd')
    round_2_series = tree.xpath('//*[@id="my-teams-table"]/div[1]/div/div[5]/dl/dd')
    round_3_series = tree.xpath('//*[@id="my-teams-table"]/div[1]/div/div[6]/dl/dd')
    round_4_series = tree.xpath('//*[@id="my-teams-table"]/div[1]/div/div[7]/dl/dd')

    #get round_1
    round_data = []
    for this_round in [round_1, round_2,round_3, round_4]:
        for game in this_round:
            try:
                game_text = game.text_content()
                round_data.append("(" + game_text.split("(")[1])
                round_data.append("(" + game_text.split("(")[2])
            except:
                round_data.append("")
                round_data.append("")

    #get series score
    round_series_data_array = []
    for this_round in [round_1_series, round_2_series,round_3_series, round_4_series]:
        for game_series in this_round:
            try:
                game_score = game_series.text_content()
                round_data.append(game_score[0:1])
                round_data.append(game_score[len(game_score)-1:len(game_score)])                
            except:
                round_data.append("")
                round_data.append("")

    #for k,i in enumerate(round_data):
    #    print k, i
    #print len(round_data)
    
    round_1_1 = ""
    if int(round_data[38])> int(round_data[39]):
        round_1_1 = round_data[8].split(" ")[1] + " " + round_data[38] + " " + round_data[39]
    elif int(round_data[40])> int(round_data[39]):
        round_1_1 = round_data[9].split(" ")[1] + " " + round_data[38] + " " + round_data[39]
    else:
        round_1_1 = "TIED " + round_data[38] + " " + round_data[39]
    

    round_1_2 = ""
    if int(round_data[40])> int(round_data[41]):
        round_1_2 = round_data[10].split(" ")[1] + " " + round_data[40] + "-" + round_data[41]
    elif int(round_data[41])> int(round_data[40]):
        round_1_2 = round_data[11].split(" ")[1] + " " + round_data[40] + "-" + round_data[41]
    else:
        round_1_2 = "TIED " + round_data[40] + "-" + round_data[41]
    
    round_1_3 = ""
    if int(round_data[42])> int(round_data[43]):
        round_1_3 = round_data[12].split(" ")[1] + " " + round_data[42] + "-" + round_data[43]
    elif int(round_data[43])> int(round_data[42]):
        round_1_3 = round_data[13].split(" ")[1] + " " + round_data[42] + "-" + round_data[43]
    else:
        round_1_3 = "TIED " + round_data[42] + "-" + round_data[43]

    round_1_4 = ""
    if int(round_data[44])> int(round_data[45]):
        round_1_4 = round_data[14].split(" ")[1] + " " + round_data[44] + "-" + round_data[45]
    elif int(round_data[45])> int(round_data[44]):
        round_1_4 = round_data[15].split(" ")[1] + " " + round_data[44] + "-" + round_data[45]
    else:
        round_1_4 = "TIED " + round_data[44] + "-" + round_data[45]
        
    round_1_5 = ""
    if int(round_data[30])> int(round_data[31]):
        round_1_5 = round_data[0].split(" ")[1] + " " + round_data[30] + "-" + round_data[31]
    elif int(round_data[31])> int(round_data[30]):
        round_1_5 = round_data[1].split(" ")[1] + " " + round_data[30] + "-" + round_data[31]
    else:
        round_1_5 = "TIED " + round_data[30] + "-" + round_data[31]
        
    round_1_6 = ""
    if int(round_data[32])> int(round_data[33]):
        round_1_6 = round_data[2].split(" ")[1] + " " + round_data[32] + "-" + round_data[33]
    elif int(round_data[33])> int(round_data[32]):
        round_1_6 = round_data[3].split(" ")[1] + " " + round_data[32] + "-" + round_data[33]
    else:
        round_1_6 = "TIED " + round_data[32] + "-" + round_data[33]
        
    round_1_7 = ""
    if int(round_data[34])> int(round_data[35]):
        round_1_7 = round_data[4].split(" ")[1] + " " + round_data[34] + "-" + round_data[35]
    elif int(round_data[35])> int(round_data[34]):
        round_1_7 = round_data[5].split(" ")[1] + " " + round_data[34] + "-" + round_data[35]
    else:
        round_1_7 = "TIED " + round_data[34] + "-" + round_data[35]
        
    round_1_8 = ""
    if int(round_data[36])> int(round_data[37]):
        round_1_8 = round_data[6].split(" ")[1] + " " + round_data[36] + "-" + round_data[37]
    elif int(round_data[37])> int(round_data[36]):
        round_1_8 = round_data[7].split(" ")[1] + " " + round_data[36] + "-" + round_data[37]
    else:
        round_1_8 = "TIED " + round_data[36] + "-" + round_data[37]
    
    round_2_1 = ""
    round_2_2 = ""
    round_2_3 = ""
    round_2_4 = ""
    round_3_1 = ""
    round_3_2 = ""
    round_4_1 = ""

    #check if round 2 is started    
    if isinstance(round_data[46], str):
        if int(round_data[50])> int(round_data[51]):
            round_2_1 = round_data[20].split(" ")[1] + " " + round_data[50] + "-" + round_data[51]
        elif int(round_data[51])> int(round_data[50]):
            round_2_1 = round_data[21].split(" ")[1] + " " + round_data[50] + "-" + round_data[51]
        else:
            round_2_1 = "TIED " + round_data[36] + "-" + round_data[37]

        if int(round_data[52])> int(round_data[53]):
            round_2_1 = round_data[22].split(" ")[1] + " " + round_data[52] + "-" + round_data[53]
        elif int(round_data[53])> int(round_data[52]):
            round_2_1 = round_data[23].split(" ")[1] + " " + round_data[52] + "-" + round_data[53]
        else:
            round_2_1 = "TIED " + round_data[52] + "-" + round_data[53]

        if int(round_data[46])> int(round_data[47]):
            round_2_1 = round_data[16].split(" ")[1] + " " + round_data[46] + "-" + round_data[47]
        elif int(round_data[47])> int(round_data[46]):
            round_2_1 = round_data[17].split(" ")[1] + " " + round_data[46] + "-" + round_data[47]
        else:
            round_2_1 = "TIED " + round_data[46] + "-" + round_data[47]

        if int(round_data[48])> int(round_data[49]):
            round_2_1 = round_data[18].split(" ")[1] + " " + round_data[48] + "-" + round_data[49]
        elif int(round_data[49])> int(round_data[48]):
            round_2_1 = round_data[19].split(" ")[1] + " " + round_data[48] + "-" + round_data[49]
        else:
            round_2_1 = "TIED " + round_data[48] + "-" + round_data[49]
    
    #check if round 3 is started    
    if isinstance(round_data[54], str):
        if int(round_data[56])> int(round_data[57]):
            round_3_1 = round_data[26].split(" ")[1] + " " + round_data[56] + "-" + round_data[57]
        elif int(round_data[57])> int(round_data[56]):
            round_3_1 = round_data[27].split(" ")[1] + " " + round_data[56] + "-" + round_data[57]
        else:
            round_3_1 = "TIED " + round_data[56] + "-" + round_data[57]

        if int(round_data[54])> int(round_data[55]):
            round_3_2 = round_data[24].split(" ")[1] + " " + round_data[54] + "-" + round_data[55]
        elif int(round_data[55])> int(round_data[54]):
            round_3_2 = round_data[25].split(" ")[1] + " " + round_data[54] + "-" + round_data[55]
        else:
            round_3_2 = "TIED " + round_data[54] + "-" + round_data[55]

    #check if round 4 is started    
    if isinstance(round_data[59], str):
        print "round 4 started"
        if int(round_data[59])> int(round_data[58]):
            round_2_1 = round_data[29].split(" ")[1] + " " + round_data[36] + "-" + round_data[37]
        elif int(round_data[58])> int(round_data[59]):
            round_2_1 = round_data[28].split(" ")[1] + " " + round_data[36] + "-" + round_data[37]
        else:
            round_2_1 = "TIED " + round_data[59] + "-" + round_data[58]

    #row 1
    playoff_table += "| " + round_data[8] + " | " + round_1_1 + "||||" + round_1_5 + " | " + round_data[0] + " |\n"
    #row 2
    playoff_table += "| " + round_data[9] + " ||" + round_2_1 + "||" + round_2_3 + "|| " + round_data[1] + " |\n"
    #row 3
    playoff_table += "||||||||\n"
    #row 4
    playoff_table += "| " + round_data[10] + " | " + round_1_2 + "||" + round_3_1 + "||" + round_1_6 + " | " + round_data[2] + " |\n"
    #row 5
    playoff_table += "| " + round_data[11] + " |||"+ round_4_1 +"||| " + round_data[3] + " |\n"
    #row 6
    playoff_table += "||||||||\n"
    #row 7
    playoff_table += "| " + round_data[12] + " | " + round_1_3 + "||" + round_3_2 + "||" + round_1_7 + " | " + round_data[4] + " |\n"
    #row 8
    playoff_table += "| " + round_data[13] + " ||" + round_2_2 + "||" + round_2_4 + "||" + round_data[5] + " |\n"
    #row 9
    playoff_table += "||||||||\n"
    #row 10
    playoff_table += "| " + round_data[14] + " | " + round_1_4 + "||||" + round_1_8 + " | " + round_data[6] + " |\n"
    #row 11
    playoff_table += "| " + round_data[15] + " ||" + round_2_4 + "|||| " + round_data[7] + " |\n"

    #List of NBA city names
    city_names = ['Boston','Brooklyn','New York','Philadelphia','Toronto',
                  'Chicago','Cleveland','Detroit','Indiana','Milwaukee',
                  'Atlanta','Charlotte','Miami','Orlando','Washington',
                  'Golden State','Golden St','LA','Los Angeles Clippers',
                  'Los Angeles Lakers','Phoenix','Sacramento','Dallas','Houston',
                  'Memphis','New Orleans','San Antonio','Denver','Minnesota',
                  'Oklahoma City','Portland','Philadelphia','Utah', 'San'
                  ]
    #Corresponding list of hrefs
    hrefs = ['[](/BOS)','[](/BKN)','[](/NYK)','[](/PHI)','[](/TOR)',
             '[](/CHI)','[](/CLE)','[](/DET)','[](/IND)','[](/MIL)',
             '[](/ATL)','[](/CHA)','[](/MIA)','[](/ORL)','[](/WAS)',
             '[](/GSW)','[](/GSW)','[](/LAC)','[](/LAC)',
             '[](/LAL)','[](/PHX)','[](/SAC)','[](/DAL)','[](/HOU)',
             '[](/MEM)','[](/NOP)','[](/SAS)','[](/DEN)','[](/MIN)',
             '[](/OKC)','[](/POR)','[](/PHI)','[](/UTA)', '[](/SAS)'
             ]

    for city,href in zip(city_names,hrefs):
        #Replace all of the city names with hrefs
        playoff_table = playoff_table.replace(city,href)
    
    return playoff_table


def get_standings_nba():
    """Get standings from data.nba.com """
    
    url = "http://data.nba.com/json/cms/2016/standings/conference.json"
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
                  'Oklahoma City','Portland','Philadelphia','Utah', 
                  ]
    #Corresponding list of hrefs
    hrefs = ['**BOS**','**BKN**','**NYK**','**PHI**','**TOR**',
             '**CHI**','**CLE**','**DET**','**IND**','**MIL**',
             '**ATL**','**CHA**','**MIA**','**ORL**','**WAS**',
             '**GSW**','**GSW**','**LAC**','**LAL**','**LAC**',
             '**LAL**','**PHX**','**SAC**','**DAL**','**HOU**',
             '**MEM**','**NOP**','**SAS**','**DEN**','**MIN**',
             '**OKC**','**POR**','**PHI**','**UTA**',
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
