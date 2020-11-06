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
PROD_ENV = True


#----------


app = Flask(__name__)
app.secret_key = b'\x06)\x8e\xa3BW"\x9d\xcd\x1d5)\xd6\xd1b1'


# obtains username
def get_username():
    if PROD_ENV:
        username = CASClient().authenticate()
        print(username)
        return username

    else:
        return 'batyas'


# if user in group, gets groupname and id stored in cookie
# if nothing stored, defaults to first group in list of user's groups
def getCurrGroupnameAndId(request, groups, inGroup=True):
    groupname = request.cookies.get('groupname')
    print(groupname)
    if groupname == None and inGroup:
        groupname = groups[0][1]

    groupid = request.cookies.get('groupid')
    print(groupid)
    if groupid == None and inGroup:
        groupid = groups[0][0]
    elif inGroup: groupid = int(groupid)
    return groupname, groupid

# returns bool - is user owner or manager
# (used to display manage group tab in navbar if relevant)
def getIsMgr(username, inGroup, request, groups=None):
    if inGroup:
        if groups == None:
            groups = get_user_groups(username)
        _, groupid = getCurrGroupnameAndId(request, groups)
        role = get_user_role(username, groupid)
        if role == -1:
            return role
        return (role in ['manager','owner'])
    else:
        return False

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

def military_to_us_time(time):
    if int(time.split(':')[0]) == 0:
        time = "12:00 AM"
    elif int(time.split(':')[0]) < 12:
        time = str(int(time.split(":")[0])) + ":00 AM"
    elif int(time.split(':')[0]) > 12:
        time = str(int(time.split(":")[0]) - 12) + ":00 PM"
    return time

def shifts_to_us_time(shifts):
    for i in shifts:
        shifts[i][1] = military_to_us_time(shifts[i][1])
        shifts[i][2] = military_to_us_time(shifts[i][2])
    return shifts

def formatDisplaySched(currsched):
    days_to_nums = {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6}
    nums_to_days = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}

    if currsched: 
        keys = sorted(currsched.keys())
        schedStrings = {}
        for key in keys:
            split = key.split('_')
            shiftString = "{} {} - {}".format(nums_to_days[int(split[0])],military_to_us_time(split[1]), military_to_us_time(split[2]))
            schedStrings[shiftString] = currsched[key]
        currsched = schedStrings
    else: currsched = {}
    return currsched

#------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET','POST'])
def index():
    print('visiting index')
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    groups = get_user_groups(username)
    numGroups = len(groups)
    inGroup = (numGroups != 0)
    isMgr = getIsMgr(username, inGroup, request, groups)
    if isMgr == -1: groupname = groupid = None
    else: groupname, groupid = getCurrGroupnameAndId(request, groups, inGroup)
    print(groupname, groupid, "at index")
    groups_by_name = [g[1] for g in groups]

    if request.method == 'GET':
        html = render_template('index.html', groups=groups_by_name, groupname=groupname, numGroups=numGroups, inGroup=inGroup, isMgr=isMgr)
        response = make_response(html)
        return response

    else:
        groupname = request.form['groupname']
        groupid = get_group_id(groupname)
        isMgr = (get_user_role(username, groupid) in ["manager", "owner"])

        html = render_template('index.html',groups=groups_by_name, groupname=groupname, numGroups=numGroups, inGroup=inGroup, isMgr=isMgr)
        response = make_response(html)
        response.set_cookie('groupname', groupname)
        response.set_cookie('groupid', str(groupid))
        return response

@app.route('/profile',methods=['GET'])
def profile():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    userInfo = get_profile_info(username)
    inGroup = in_group(username)
    isMgr = getIsMgr(username, inGroup, request)

    globalPreferences = blankSchedule()
    try:
        globalPreferences = get_double_array(get_global_preferences(username))
    except Exception:
        pass

    html = render_template('profile.html', firstName=userInfo.firstname, lastName=userInfo.lastname, netid=username, email=userInfo.email, 
        phoneNum=userInfo.phone, schedule=globalPreferences, inGroup=inGroup, isMgr=isMgr, editable=False)

    response = make_response(html)

    return response

@app.route('/manage', methods=['GET','POST'])
def manage():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    groups = get_user_groups(username)

    if len(groups) == 0:
        return redirect(url_for('index'))

    numGroups = len(groups)
    inGroup = (numGroups != 0)
    isMgr = getIsMgr(username, inGroup, request, groups)
    users = get_all_users()
    users.remove(username)
    
    if not isMgr:
        return redirect(url_for('index'))

    groupname, groupid = getCurrGroupnameAndId(request, groups, inGroup)
    curr_members = get_group_users(groupid)

    selected = {}
    for user in users:
        selected[user] = False
    for member in curr_members:
        selected[member] = True

    print(selected)

    shifts = get_group_shifts(groupid)
    if not shifts:
        shifts = {}
    
    currsched = get_group_schedule(groupid)
    currsched = formatDisplaySched(currsched)
    
    if request.method == 'GET':
        shifts = shifts_to_us_time(shifts)
        html = render_template('manage.html', groupname=groupname, inGroup=inGroup, isMgr=isMgr, shifts=shifts, users=users, selected=selected, currsched=currsched)
        response = make_response(html)
        return response

    else:
        groupid = get_group_id(groupname)

        if request.form["submit"] == "Add":
            days_to_nums = {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6}

            day = request.form["day"]
            start = request.form["start"]
            end = request.form["end"]
            npeople = request.form["npeople"]
            
            shift = [day, start, end, npeople]
            shiftid = "{}_{}_{}".format(days_to_nums[day],start.split(":")[0],end.split(":")[0])
            shifts[shiftid]=shift
        
            # change double array of shifts to dict, update db
            change_group_shifts(groupid, shifts)
        elif request.form["submit"] == "Save":
            n_user_list = []
            curr_members.remove(username)
            for user in users:  # adds users
                if request.form.get(user) is not None:
                    exists = False
                    n_user_list.append(user)
                    for member in curr_members:
                        if user == member:
                            exists = True
                    if not exists:
                        add_user_to_group(groupid, user, 'member')
                        print("added user" + user)
            for member in curr_members:  # removes users
                remains = False
                for user in n_user_list:
                    if member == user:
                        remains = True
                        print("user remains" + user)
                if not remains:
                    remove_user_from_group(member, groupid)
                    print("removed" + member)

            selected = {}
            for user in users:
                selected[user] = False
            for n_user in n_user_list:
                selected[n_user] = True
        elif request.form["submit"] == "Delete":
            remove_group(groupid)
            groups = get_user_groups(username)
            inGroup = (len(groups) > 0)
            if inGroup:
                groupid = groups[0][0]
                groupname = groups[0][1]
            response = make_response(redirect(url_for("index")))
            response.set_cookie('groupname', groupname)
            response.set_cookie('groupid', str(groupid))
            return response
        elif request.form["submit"] == "Generate Schedule":
            try:
                currsched = generate_schedule(groupid)
            except:
                currsched = None
            if (currsched == {}):
                currsched = None

            if currsched is not None:
                change_group_schedule(groupid, currsched)
                currsched = formatDisplaySched(currsched)
                # reset weekly group prefs of all group members
                groupmems = get_group_members(groupid)
                for mem in groupmems:
                    change_user_preferences_group(groupid, mem)
        else:
            shiftid = request.form["submit"]
            del shifts[shiftid]
            change_group_shifts(groupid, shifts)
        shifts = shifts_to_us_time(shifts)
        html = render_template('manage.html', groupname=groupname, inGroup=inGroup, isMgr=isMgr, shifts=shifts, users=users, selected=selected, currsched=currsched)
        response = make_response(html)
        return response

@app.route('/schedule', methods=['GET'])
def schedule():
    username = get_username()
    
    if not (user_exists(username)):
        return redirect(url_for('createProfile'))
    
    groups = get_user_groups(username)

    if len(groups) == 0:
        return redirect(url_for('index'))

    groupname, groupid = getCurrGroupnameAndId(request, groups)
    isMgr = getIsMgr(username, True, request, groups)
    
    groupsched = get_group_schedule(groupid)
    if groupsched is not None:
        schedule = get_double_array(parse_user_schedule(username, groupsched))
    else:
        schedule = groupsched
    
    shifts = get_group_shifts(groupid)
    if not shifts:
        shifts = {}
    else:
        shifts = shifts_to_us_time(shifts)
       

    html = render_template('schedule.html', schedule=schedule , groupname=groupname, inGroup=True, isMgr=isMgr, editable=False,
        shifts=shifts)
    response = make_response(html)

    return response

@app.route('/group', methods=['GET'])
def group():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    groups = get_user_groups(username)

    if len(groups) == 0:
        return redirect(url_for('index'))

    groupname, groupid = getCurrGroupnameAndId(request, groups)
    isMgr = getIsMgr(username, True, request, groups)

    groupprefs = get_group_preferences(groupid, username)
    if groupprefs == None:
        change_user_preferences_global(username, create_preferences(blankSchedule()))
        groupprefs = get_global_preferences(username)
    weeklyPref = get_double_array(groupprefs)
        
    # later add code to reset groupprefs to global prefs on sunday

    notifPrefs = get_group_notifications(username, groupid)
    if notifPrefs != None and notifPrefs != -1: 
        prevphonePref = notifPrefs.textnotif
        prevemailPref = notifPrefs.emailnotif
    else:
        prevemailPref = False
        prevphonePref = False

    html = render_template('group.html', schedule=weeklyPref, groupname=groupname, prevphonePref=prevphonePref, prevemailPref=prevemailPref, 
        inGroup=True, isMgr=isMgr, editable=False)
    response = make_response(html)
    return response

@app.route('/editGroup',methods=['GET', 'POST'])
def editGroup():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    groups = get_user_groups(username)

    if len(groups) == 0:
        return redirect(url_for('index'))

    groupname, groupid = getCurrGroupnameAndId(request, groups)
    isMgr = getIsMgr(username, True, request, groups)

    groupprefs = get_group_preferences(groupid, username)
    if groupprefs == None:
        change_user_preferences_global(username, create_preferences(blankSchedule()))
        groupprefs = get_global_preferences(username)
    weeklyPref = get_double_array(groupprefs)
        
    # later add code to reset groupprefs to global prefs on sunday

    notifPrefs = get_group_notifications(username, groupid)
    prevphonePref = notifPrefs.textnotif
    prevemailPref = notifPrefs.emailnotif

    if request.method == 'GET':
        html = render_template('editGroup.html', schedule=weeklyPref, groupname=groupname, prevphonePref=prevphonePref, prevemailPref=prevemailPref,  
            inGroup=True, isMgr=isMgr, editable=True)
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


@app.route('/populateUsers', methods=['GET'])
def populateUsers():
    add_user('John', 'Doe', 'jdoe')
    add_user('Jane', 'Doe', 'jadoe')
    add_user('Bland', 'Land', 'bland')
    add_user('Dan', 'Man', 'dman')
    add_user('Tom', 'Till', 'ttill')
    add_user('Jen', 'Jill', 'jjill')
    print("Populated Users")
    return redirect(url_for('index'))

@app.route('/cleanGroups', methods=['GET'])
def cleanGroups():
    username = get_username()

    groups = get_user_groups(username)
    if len(groups) == 0:
        return redirect(url_for('index'))
    # groups is list of tuples - (groupid, groupname), so create list of groupids from group list
    groupIds = [g[0] for g in groups]
    for groupId in groupIds:
        remove_group(groupId)
    print("DELETED ALL GROUPS")
    return redirect(url_for('index'))

@app.route('/viewGroup', methods=['GET'])
def viewGroup():
    username = get_username()
    inGroup = in_group(username)
    if not inGroup:
        return redirect(url_for('index'))
    groups = get_user_groups(username)
    isMgr = getIsMgr(username, True, request, groups)
    gName, groupId = getCurrGroupnameAndId(request, groups)
    members = get_group_users(groupId)

    html = render_template('viewGroup.html', gName=gName, members=members, inGroup=True, isMgr=isMgr)
    response = make_response(html)

    return response


@app.route('/createGroup', methods=['GET', 'POST'])
def createGroup():
    username = get_username()
    
    inGroup = in_group(username)
    isMgr = getIsMgr(username, inGroup, request)


    # names = {"bob", "joe", "jill", username}
    names = get_all_users()
    try:
        names.remove(username)
    except:  # remove method errors if element not within
        ()

    if request.method == 'GET':

        html = render_template('createGroup.html', names=names, inGroup=inGroup, isMgr=isMgr)
        response = make_response(html)
        return response

    else:
        gName = request.form['gName']
        groupId = add_group(username, gName, None)
        for name in names:
            selected = request.form.get(name) is not None
            if selected:
                add_user_to_group(groupId, name, 'member')
        response = redirect(url_for('manage'))
        response.set_cookie('groupname', gName)
        response.set_cookie('groupid', str(groupId))
        return response


@app.route('/newuser', methods=['GET', 'POST'])
def newuser():
    username = get_username()

    if user_exists(username):
        return redirect(url_for('profile'))

    html = render_template('newuser.html')
    response = make_response(html)
    return response

@app.route('/createProfile', methods=['GET', 'POST'])
def createProfile():
    username = get_username()

    if user_exists(username):
        return redirect(url_for('profile'))

    if request.method == 'GET':
        if (user_exists(username)):
            return redirect(url_for('profile'))
        html = render_template('createProfile.html', schedule=blankSchedule(), inGroup=False, isMgr=False, editable=True)
        response = make_response(html)
        return response

    else:
        fname = request.form['fname']
        lname = request.form['lname']

        email = request.form['email']
        pnum = request.form['pnumber']

        # notification preferences default to false currently - can change if wanted
        preftext = False
        prefemail = False

        globalPreferences = parseSchedule()

        groupid = 1 # for prototype - add user to group one
        if not (user_exists(username)):
            add_user(fname, lname, username, email, pnum, create_preferences(globalPreferences))
            add_user_to_group(groupid, username, "member", preftext, prefemail, create_preferences(globalPreferences))
        else:
            update_profile_info(fname, lname, username, email, pnum, create_preferences(globalPreferences))

        return redirect(url_for('profile'))

@app.route('/editProfile',methods=['GET','POST'])
def editProfile():
    username = get_username()

    inGroup = in_group(username)
    isMgr = getIsMgr(username, inGroup, request)

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
            prevemail=prevemail, prevphoneNum=prevphoneNum, schedule=prevGlobalPreferences, inGroup=inGroup, isMgr=isMgr, editable=True)
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
