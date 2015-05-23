#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
models.py
--------------

Data models for Game Thread Chat.

"""
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

from initiate import db

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String, unique=False)
    players = db.relationship('Player', backref='team',
                                lazy='dynamic')

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String, unique=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
