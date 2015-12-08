#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
app.py
--------------

Main flask app for NBA_MOD.

"""

import os
import json

from flask import Flask, flash, render_template, session, request, redirect, url_for, jsonify
import praw
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import utils
from models import *

app = Flask(__name__)
NBA_MOD_REDIRECT_URL = os.environ['NBA_MOD_REDIRECT_URL']
NBA_MOD_CLIENT_ID = os.environ['NBA_MOD_CLIENT_ID']
NBA_MOD_SECRET = os.environ['NBA_MOD_SECRET']
app.config['SECRET_KEY'] = os.environ['NBA_MOD_SECRET']
r = praw.Reddit('OAuth gamethread chat by /u/catmoon')
r.set_oauth_app_info(NBA_MOD_CLIENT_ID, NBA_MOD_SECRET, NBA_MOD_REDIRECT_URL)
authorize_url = r.get_authorize_url('DifferentUniqueKey','identity',refreshable = True)


@app.route('/')
def home():
	#authorize_url = r.get_authorize_url('DifferentUniqueKey','identity edit submit',refreshable = True)
    return render_template('player_flair.html',authorize_url=authorize_url)

@app.route('/player_flair')
def player_flair():
    #authorize_url = r.get_authorize_url('DifferentUniqueKey','identity edit submit',refreshable = True)
    return render_template('player_flair.html',authorize_url=authorize_url)

#OAuth2 with reddit 
@app.route("/auth/", methods = ['GET'])
def auth():
	code = request.args.get('code', '')
	info = r.get_access_information(code)
	r.set_access_credentials(**info)
	user = r.get_me()
	session['username'] = user.name
	return redirect(url_for('home'))

#Autocomplete
@app.route('/autocomplete')
def autocomplete():
    search_input = request.args.get('search_input',type=str)
    team_input = request.args.get('team_input',type=str)
    players = utils.fetch_search(search_input, team_input)
    player_list = []
    for player in players:
        #handle mislabeling of NOP
        if player["team_name"]=="NOH":
            player_list.append("[NOP] " + player["player_name"])
        else:
            player_list.append("[" + player["team_name"] + "] " + player["player_name"])
    return jsonify(results=player_list)

#Logout
@app.route('/logout')
def logout():
	session['username'] = ""
	return jsonify(success=[])


#Autocomplete
@app.route('/submit')
def submit():
    user = session['username']
    flair_text = request.args.get('flair_text',type=str)
    flair_class = request.args.get('flair_class',type=str)
    success = utils.update_flair(user,flair_text,flair_class.replace('flair-',''))
    print success
    return jsonify(success=[])

#flair stats
@app.route('/flair_stats')
def flair_stats():
    return render_template('flair_stats.html')

@app.route('/_flair_list')
def flair_list():
    print "request made"
    flair = db.session.query(Flair).order_by(Flair.id.desc()).first()
    flairjson = json.loads(flair.jsondata.decode('string-escape').strip('"'))
    #flairjson = json.loads('[{"jflair": {"color": "rgba(159,234,231)", "number":1}}]')
    flair_list = []
    for item in flairjson:
        flair_list.append(item["jflair"])

    return jsonify(flair_list=flair_list, last_updated=flair.date)


if __name__ == "__main__":
    engine = create_engine("postgres://bvbaezxfnrmxev:YYESfSaRGDrxWPrZr8JuAdpoXY@ec2-23-23-188-252.compute-1.amazonaws.com:5432/ddvahv1uqndlvb")
    Session = sessionmaker(bind=engine)    
    session = Session()
    session._model_changes = {}
    app.run(debug=True)