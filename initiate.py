#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
initiate.py
--------------

Initiate data for app.

"""
import sys
import os

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

initiate_app=Flask(__name__)
initiate_app.secret_key=os.environ['SECRET_KEY']
initiate_app.config['SQLALCHEMY_DATABASE_URI']="postgres://bvbaezxfnrmxev:YYESfSaRGDrxWPrZr8JuAdpoXY@ec2-23-23-188-252.compute-1.amazonaws.com:5432/ddvahv1uqndlvb"
db=SQLAlchemy(initiate_app)

from models import *

def create_data():
    """ A helper function to create our tables and some Todo objects."""
    db.create_all()
    db.session.commit()

if __name__ == '__main__':
    
    if '-c' in sys.argv:
        create_data()
    else:
        print "no command"

