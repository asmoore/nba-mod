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
from operator import itemgetter

import praw
    
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

def get_standings():
    """Return a string markdown table of standings pulled from ESPN.
    
    """
    #Initialize lists
    team_list = [];
    W_list = [];
    L_list = [];
    west = [];
    east = [];
    #Create headers for standings
    standings = '''\n\n**STANDINGS**\n\n
|EAST|||WEST|||
|:---:|:---:|:---:|:---:|:---:|:---:|
|**TEAM**|*W/L*|*GB*|**TEAM**|*W/L*|*GB*|\n'''
    
    #Open ESPN        
    tree = html.parse('http://espn.go.com/nba/standings/_/group/3')
    #Get teams from URL
    teams = tree.xpath('(//table[@class="tablehead"]/tr)/td//a[1]')
    #Get corresponding wins
    W = tree.xpath('(//table[@class="tablehead"]/tr)/td[2]')
    #Get corresponding losses
    L = tree.xpath('(//table[@class="tablehead"]/tr)/td[3]')

    #Go through teams and add them to team_list
    for j in range(0,len(teams)):
        if str(teams[j].text) != "None" and str(teams[j].text) != "W" and str(teams[j].text) != "L" and str(teams[j].text) != "PCT" and str(teams[j].text) != "GB" and str(teams[j].text) != "HOME" and str(teams[j].text) != "ROAD" and str(teams[j].text) != "DIV" and str(teams[j].text) != "CONF" and str(teams[j].text) != "PF" and str(teams[j].text) != "PA" and str(teams[j].text) != "STRK":
            #print teams[j].text
            team_list.append(teams[j].text)
    #Go through W and add them to W_list     
    for j in range(0,len(W)):
        if str(W[j].text) != "None":
            #print W[j].text
            W_list.append(W[j].text)
    #Go through L and add them to L_list
    for j in range(0,len(L)):
        if str(L[j].text) != "None":
            #print L[j].text
            L_list.append(L[j].text)

    #Create markdown table split into two tables (EAST, WEST)
    for j in range(0,15):
        if(float(W_list[j])+float(L_list[j])>0):
            wpct = float(W_list[j])/(float(W_list[j])+float(L_list[j]))
        else:
            wpct = 0;
        east.append({'team':team_list[j],'W':W_list[j],'L':L_list[j],'wpct':wpct})
        if(float(W_list[j+15])+float(L_list[j+15])>0):
            wpct = float(W_list[j+15])/(float(W_list[j+15])+float(L_list[j+15]))
        else:
            wpct=0;
        west.append({'team':team_list[j+15],'W':W_list[j+15],'L':L_list[j+15],'wpct':wpct})

    east_sorted = newlist = sorted(east, key=itemgetter('wpct'),reverse=True)
    west_sorted = newlist = sorted(west, key=itemgetter('wpct'),reverse=True)

    #ensure division leaders are in top 4
    if east[0]['wpct']<=east_sorted[4]['wpct']:
        east[0]['wpct'] = east_sorted[4]['wpct']+.01
    if east[5]['wpct']<=east_sorted[4]['wpct']:
        east[5]['wpct'] = east_sorted[4]['wpct']+.01
    if east[10]['wpct']<=east_sorted[4]['wpct']:
        east[10]['wpct'] = east_sorted[4]['wpct']+.01
    if west[0]['wpct']<=west_sorted[4]['wpct']:
        west[0]['wpct'] = west_sorted[4]['wpct']+.01
    if west[5]['wpct']<=west_sorted[4]['wpct']:
        west[5]['wpct'] = west_sorted[4]['wpct']+.01
    if west[10]['wpct']<=west_sorted[4]['wpct']:
        west[10]['wpct'] = west_sorted[4]['wpct']+.01

    east = newlist = sorted(east, key=itemgetter('wpct'),reverse=True)
    west = newlist = sorted(west, key=itemgetter('wpct'),reverse=True)

    for j in range(0,15):
        gb = ((float(east[0]['W'])-float(east[0]['L']))-(float(east[j]['W'])-float(east[j]['L'])))/2
        if j<8:
            standings = standings+'|'+str(j+1)+' '+east[j]['team']+'|'+east[j]['W']+'-'+east[j]['L']+'|'+str(gb)
        else:
            standings = standings+'|'+east[j]['team']+'|'+east[j]['W']+'-'+east[j]['L']+'|'+str(gb)
        gb = ((float(west[0]['W'])-float(west[0]['L']))-(float(west[j]['W'])-float(west[j]['L'])))/2
        if j<8:
            standings = standings+'|'+str(j+1)+' '+west[j]['team']+'|'+west[j]['W']+'-'+west[j]['L']+'|'+str(gb)+'|'
        else:
            standings = standings+'|'+west[j]['team']+'|'+west[j]['W']+'-'+west[j]['L']+'|'+str(gb)+'|'
        
        standings = standings+'\n'
    #Replace city names with href tags
    standings = city_names_to_subs(standings)
    standings = standings + "\n\n"
    return standings

def get_standings_nba():
    url = "http://data.nba.com/json/cms/2014/standings/conference.json"
    req = urllib2.urlopen(url).read()
    obs = json.loads(req)
    obs["sports_content"]["standings"]["conferences"]["East"]["team"][11]["team_stats"]["rank"]

    standings = """|EAST|||WEST|||
    |:---:|:---:|:---:|:---:|:---:|:---:|
    |**TEAM**|*W/L*|*GB*|**TEAM**|*W/L*|*GB*|
    """

    for i in range(0,15):
        east = obs["sports_content"]["standings"]["conferences"]["East"]["team"][i]
        east_name = east["abbreviation"]
        east_record = east["team_stats"]["wins"] + "-" + east["team_stats"]["losses"]
        east_gb_conf = east["team_stats"]["gb_conf"]
        west = obs["sports_content"]["standings"]["conferences"]["West"]["team"][i]
        west_name = west["abbreviation"]
        west_record = west["team_stats"]["wins"] + "-" + west["team_stats"]["losses"]
        west_gb_conf = west["team_stats"]["gb_conf"]
        if i < 8:
            standings = standings + "|" + str(i+1) + " [](/" + east_name + ")| " + east_record + " | " + east_gb_conf + "|" + str(i+1) + " [](/" + west_name + ")| " + west_record + " | " + west_gb_conf + " |\n"
        else:
            standings = standings + "|[](/" + east_name + ")| " + east_record + " | " + east_gb_conf + " |[](/" + west_name + ")| " + west_record + " | " + west_gb_conf + " |\n"
            
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

