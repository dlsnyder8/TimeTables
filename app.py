from flask import Flask
from flask import render_template, make_response, request, redirect, url_for
from CASClient import CASClient
from database import get_profile_info, add_user
import os
from sys import stderr, exit
import urllib.parse as urlparse

#-------------------
# CAS Authentication cannot be run locally unfortunately
# Set this variable to False if local, and change to True before pushing
PROD_ENV = False


#----------


app = Flask(__name__)
app.secret_key = b'\x06)\x8e\xa3BW"\x9d\xcd\x1d5)\xd6\xd1b1'




@app.route('/',methods=['GET'])
@app.route('/index',methods=['GET'])
def index():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test123'
    html = render_template('index.html')
    response = make_response(html)
    

    return response



@app.route('/profile',methods=['GET'])
def profile():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test123'
    # is netid = username?
    # get groupid from cookie that takes info from input into index page
    groupid = 1
    userInfo, notifPrefs = get_profile_info(username, groupid)
    html = render_template('profile.html', firstName = userInfo.firstname, lastName = userInfo.lastname, netid=username, email=userInfo.email, phoneNum=userInfo.phone, phonePref=notifPrefs.emailnotif, emailPref=notifPrefs.textnotif)
    response = make_response(html)

    return response



@app.route('/schedule', methods=['GET'])
def schedule():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test123'

    html = render_template('schedule.html')
    response = make_response(html)

    return response

@app.route('/groupInfo', methods=['GET'])
def groupInfo():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test123'

    html = render_template('groupInfo.html')
    response = make_response(html)

    return response


@app.route('/createProfile',methods=['GET','POST'])
def createProfile():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        # for test purposes
        username = 'batyas'

    # add error handling if username already exists in database

    if request.method == 'GET':
        html = render_template('createProfile.html')
        response = make_response(html)
        return response

    else:
        fname = request.form['fname']
        lname = request.form['lname']

        email = request.form['email']
        pnum = request.form['pnumber']
        #preftext = request.args.get('preftext')
        #prefemail = request.args.get('prefemail')
        add_user(fname, lname, username, email, pnum)

        return redirect(url_for('profile'))


if __name__ == '__main__':
    app.run()
