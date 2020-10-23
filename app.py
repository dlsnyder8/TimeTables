from flask import Flask
from flask import render_template, make_response, request, redirect, url_for
from CASClient import CASClient
from database import *
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

# takes a request and returns the schedule values
def parseSchedule():
    table_values = []
    slot_num = 24  # number of time slots in schedule, should be even
    for i in range(slot_num):  # iterates through time slots
        time = i
        week = []
        for day in range(7):  # iterates through days in a week
            if i < (slot_num/2):
                split = "0"
            else:
                split = "1"
            hour = time % 12
            if hour == 0:
                hour = 12
            str_call = str(hour) + "-" + str(1+((time) % 12)) + "-" + str(split) + "-" + str(day)
            week.append(request.form.get(str_call))
        table_values.append(week)

    for i in range(len(table_values)):
        for j in range(len(table_values[i])):
            if table_values[i][j] is None:
                table_values[i][j] = False
            else:
                table_values[i][j] = True

    return table_values


# creates a test schedule
def testSchedule():
    table_values = []
    slot_num = 24  # number of time slots in schedule, should be even
    for i in range(slot_num):  # iterates through time slots
        week = []
        for day in range(7):  # iterates through days in a week
            if day % 2 == 0:
                week.append(True)
            else:
                week.append(False)
        table_values.append(week)
    return table_values


# creates a blank schedule
def blankSchedule():
    table_values = []
    slot_num = 24  # number of time slots in schedule, should be even
    for i in range(slot_num):  # iterates through time slots
        week = []
        for day in range(7):  # iterates through days in a week
            week.append(False)
        table_values.append(week)
    return table_values


@app.route('/',methods=['GET'])
@app.route('/index',methods=['GET'])
def index():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2'
    html = render_template('index.html')
    response = make_response(html)

    return response



@app.route('/profile',methods=['GET'])
def profile():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2'

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))
    # is netid = username?
    # get groupid from cookie that takes info from input into index page
    groupid = 1
    userInfo, notifPrefs = get_profile_info(username, groupid)

    globalPreferences = blankSchedule()
    try:
        globalPreferences = get_double_array(get_global_preferences(username))
    except Exception:
        pass

    html = render_template('profile.html', firstName=userInfo.firstname, lastName=userInfo.lastname, netid=username, email=userInfo.email, phoneNum=userInfo.phone, phonePref=notifPrefs.emailnotif, emailPref=notifPrefs.textnotif, schedule=globalPreferences, editable=False)
    response = make_response(html)

    return response



@app.route('/schedule', methods=['GET'])
def schedule():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2'
    
    if not (user_exists(username)):
        return redirect(url_for('createProfile'))


    globalPreferences = get_double_array(get_global_preferences(username))

    html = render_template('schedule.html', schedule=globalPreferences, editable=False)
    response = make_response(html)

    return response

@app.route('/groupInfo', methods=['GET'])
def groupInfo():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2'

    html = render_template('groupInfo.html')
    response = make_response(html)

    return response


@app.route('/createProfile', methods=['GET', 'POST'])
def createProfile():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        # for test purposes
        username = 'test2'

    # add error handling if username already exists in database

    if request.method == 'GET':
        if (user_exists(username)):
            return redirect(url_for('profile'))
        html = render_template('createProfile.html', schedule=blankSchedule(), editable=True)
        response = make_response(html)
        return response

    else:
        fname = request.form['fname']
        lname = request.form['lname']

        email = request.form['email']
        pnum = request.form['pnumber']
        preftext = request.form.get('preftext')
        prefemail = request.form.get('prefemail')
        
        if preftext == 'on': 
            preftext = True
        else:
            preftext = False
        if prefemail == 'on': 
            prefemail = True
        else:
            prefemail = False

        globalPreferences = parseSchedule()
        print(globalPreferences)

        groupid = 1 # for prototype - add user to group one
        if not (user_exists(username)):
            add_user(fname, lname, username, email, pnum, create_preferences(globalPreferences))
            add_user_to_group(groupid, username, "member", preftext, prefemail, create_preferences(globalPreferences))
        else:
            update_user(fname, lname, username, email, pnum, preftext, prefemail, create_preferences(globalPreferences))
        

        return redirect(url_for('profile'))

@app.route('/editProfile',methods=['GET','POST'])
def editProfile():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2'

    # add error handling if username already exists in database

    groupid = 1
    userInfo, notifPrefs = get_profile_info(username, groupid)
    prevfirstName = userInfo.firstname
    prevlastName = userInfo.lastname
    prevemail = userInfo.email
    prevphoneNum = userInfo.phone
    prevphonePref = notifPrefs.emailnotif
    prevemailPref = notifPrefs.textnotif

    prevGlobalPreferences = blankSchedule()
    try:
        prevGlobalPreferences = get_double_array(get_global_preferences(username))
    except Exception:
        pass

    if request.method == 'GET':
        html = render_template('editProfile.html', prevfname=prevfirstName, prevlname=prevlastName, \
            prevemail=prevemail, prevphoneNum=prevphoneNum, prevphonePref=prevphonePref, prevemailPref=prevemailPref, \
                schedule=prevGlobalPreferences, editable=True)
        response = make_response(html)
        return response

    else:
        fname = request.form['fname']
        lname = request.form['lname']

        email = request.form['email']
        pnum = request.form['pnumber']
        preftext = request.form.get('preftext')
        prefemail = request.form.get('prefemail')

        globalPreferences = parseSchedule()

        if preftext == 'on': 
            preftext = True
        else:
            preftext = False
        if prefemail == 'on': 
            prefemail = True
        else:
            prefemail = False

        update_user(fname, lname, username, email, pnum, preftext, prefemail, create_preferences(globalPreferences))

        return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run()
