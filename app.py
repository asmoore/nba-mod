#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
app.py
--------------

Main flask app for NBA_MOD.

"""

import os

from flask import Flask, flash, render_template, session, request, redirect, url_for, jsonify
import praw

import utils

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


if __name__ == "__main__":
    app.run(debug=True)