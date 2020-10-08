from flask import Flask
from flask import render_template, make_response, request, redirect, url_for
from CASClient import CASClient
import os
import urllib.parse as urlparse

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session, create_session
from sqlalchemy.ext.automap import automap_base

DATABASE_URL = os.environ['DATABASE_URL']

app = Flask(__name__)

# create engine (db object basically)
engine = create_engine(DATABASE_URL)
#start automap and create session with automap
Base = automap_base()
Base.prepare(engine, reflect=True)

session = create_session(bind=engine)

users = Base.classes.users
groups = Base.classes.groups
group_members = Base.classes.groupmembers



@app.route('/',methods=['GET'])
@app.route('/index',methods=['GET'])
def index():
    
    html = render_template('index.html')
    response = make_response(html)
    for u in users:
        print(u.firstname)

    return response



@app.route('/profile',methods=['GET'])
def profile():
    html = render_template('profile.html')
    response = make_response(html)

    return response



@app.route('/schedule', methods=['GET'])
def schedule():
    html = render_template('schedule.html')
    response = make_response(html)

    return response

@app.route('/groupInfo', methods=['GET'])
def groupInfo():
    html = render_template('groupInfo.html')
    response = make_response(html)

    return response


@app.route('/createProfile',methods=['GET'])
def createProfile():
    html = render_template('setupProfile.html')
    response = make_response(html)

    return response


if __name__ == '__main__':
    app.run()
