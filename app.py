from flask import Flask
from flask import render_template, make_response, request, redirect, url_for
from CASClient import CASClient

from database import *
from shifttest import *

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


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET','POST'])
def index():
    if (PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2'

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    groups = get_user_groups(username)
    numGroups = len(groups)

    if request.method == 'GET':
        html = render_template('index.html', groups=groups, numGroups=numGroups)
        response = make_response(html)
        return response

    else:
        groupname = request.form['groupname']
        groupid = get_group_id(groupname)

        html = render_template('index.html',groups=groups, numGroups=numGroups)
        response = make_response(html)
        response.set_cookie('groupname',groupname)
        response.set_cookie('groupid', str(groupid))
        return response

@app.route('/profile',methods=['GET'])
def profile():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2' # or test123

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))
    
    # get groupid from cookie that takes info from input into index page
    groupid = request.cookies.get('groupid')
    if groupid == None:
        groups = get_user_groups(username)
        groupid = get_group_id(groups[0])
    else: groupid = int(groupid)

    userInfo = get_profile_info(username)
    notifPrefs = get_group_notifications(username, groupid)

    globalPreferences = blankSchedule()
    try:
        globalPreferences = get_double_array(get_global_preferences(username))
    except Exception:
        pass

    html = render_template('profile.html', firstName=userInfo.firstname, lastName=userInfo.lastname, netid=username, email=userInfo.email, phoneNum=userInfo.phone, phonePref=notifPrefs.textnotif, emailPref=notifPrefs.emailnotif, schedule=globalPreferences, editable=False)

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

    groupname = request.cookies.get('groupname')
    if groupname == None:
        groups = get_user_groups(username)
        groupaname = get_group_id(groups[0])
    
    
    globalPreferences = get_double_array(get_group_preferences(username))
    edict = solve_shift_scheduling("", "", 10, 1, ['O', 'M', 'A', 'N'], [], create_requests(globalPreferences, 0))
    

    html = render_template('schedule.html', schedule=create_schedule(edict, 0), groupname=groupname, editable=False)
    response = make_response(html)

    return response

@app.route('/group', methods=['GET'])
def group():
    if (PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2'

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    groupid = request.cookies.get('groupid')
    if groupid == None:
        groups = get_user_groups(username)
        groupid = get_group_id(groups[0])
    else: groupid = int(groupid)

    groupname = request.cookies.get('groupname')
    if groupname == None:
        groups = get_user_groups(username)
        groupaname = get_group_id(groups[0])

    groupprefs = get_group_preferences(groupid, username)
    if groupprefs == None:
        groupprefs = get_global_preferences(username)
    weeklyPref = get_double_array(groupprefs)
        
    # later add code to reset groupprefs to global prefs on sunday

    notifPrefs = get_group_notifications(username, groupid)
    prevphonePref = notifPrefs.textnotif
    prevemailPref = notifPrefs.emailnotif

    html = render_template('group.html', schedule=weeklyPref, groupname=groupname, prevphonePref=prevphonePref, prevemailPref=prevemailPref, editable=False)
    response = make_response(html)
    return response

@app.route('/editGroup',methods=['GET', 'POST'])
def editGroup():
    if (PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2'

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    groupid = request.cookies.get('groupid')
    if groupid == None:
        groups = get_user_groups(username)
        groupid = get_group_id(groups[0])
    else: groupid = int(groupid)

    groupname = request.cookies.get('groupname')
    if groupname == None:
        groups = get_user_groups(username)
        groupaname = get_group_id(groups[0])

    groupprefs = get_group_preferences(groupid, username)
    if groupprefs == None:
        groupprefs = get_global_preferences(username)
    weeklyPref = get_double_array(groupprefs)
        
    # later add code to reset groupprefs to global prefs on sunday

    notifPrefs = get_group_notifications(username, groupid)
    prevphonePref = notifPrefs.textnotif
    prevemailPref = notifPrefs.emailnotif

    if request.method == 'GET':
        html = render_template('editGroup.html', schedule=weeklyPref, groupname=groupname, prevphonePref=prevphonePref, prevemailPref=prevemailPref, editable=True)
        response = make_response(html)
        return response
    else:
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
        change_group_notifications(groupid, username, prefemail, preftext)

        prefs = create_preferences(parseSchedule())
        change_user_preferences_group(groupid, username, prefs)
        
        return redirect(url_for('group'))


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

        groupid = 1 # for prototype - add user to group one
        if not (user_exists(username)):
            add_user(fname, lname, username, email, pnum, create_preferences(globalPreferences))
            add_user_to_group(groupid, username, "member", preftext, prefemail, create_preferences(globalPreferences))
        else:
            update_profile_info(fname, lname, username, email, pnum, create_preferences(globalPreferences))
            change_group_notifications(groupid, username, prefemail, preftext)

        return redirect(url_for('profile'))

@app.route('/editProfile',methods=['GET','POST'])
def editProfile():
    if(PROD_ENV):
        username = CASClient().authenticate()
    else:
        username = 'test2'

    # add error handling if username already exists in database

    groupid = request.cookies.get('groupid')
    if groupid == None:
        groups = get_user_groups(username)
        groupid = get_group_id(groups[0])
    
    else: groupid = int(groupid)


    userInfo = get_profile_info(username)
    prevfirstName = userInfo.firstname
    prevlastName = userInfo.lastname
    prevemail = userInfo.email
    prevphoneNum = userInfo.phone

    prevGlobalPreferences = blankSchedule()
    try:
        prevGlobalPreferences = get_double_array(get_global_preferences(username))
    except Exception:
        pass

    if request.method == 'GET':
        html = render_template('editProfile.html', prevfname=prevfirstName, prevlname=prevlastName, \
            prevemail=prevemail, prevphoneNum=prevphoneNum, schedule=prevGlobalPreferences, editable=True)
        response = make_response(html)
        return response

    else:
        fname = request.form['fname']
        lname = request.form['lname']

        email = request.form['email']
        pnum = request.form['pnumber']

        globalPreferences = parseSchedule()

        update_profile_info(fname, lname, username, email, pnum, create_preferences(globalPreferences))

        return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run()
