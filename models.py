#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
models.py
--------------

Data models for flair.

"""

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

from initiate import db

class Flair(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jsondata = db.Column(db.String, unique=False)
    date = db.Column(db.String, unique=False)
