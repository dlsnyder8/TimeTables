from flask import Flask
from flask import render_template, make_response, request, redirect, url_for
from CASClient import CASClient
from flask_mail import Mail, Message

from database import *
from shifttest import *
from dates import *

import os
import json
from sys import stderr, exit
import urllib.parse as urlparse
from itertools import chain

# -------------------
# CAS Authentication cannot be run locally unfortunately
# Set this variable to False if local, and change to True before pushing
PROD_ENV = True

# ----------


app = Flask(__name__)
app.secret_key = b'\x06)\x8e\xa3BW"\x9d\xcd\x1d5)\xd6\xd1b1'
app.config.update(dict(
    DEBUG=True,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    # MAIL_USERNAME = os.environ['MAIL_USERNAME'],
    # MAIL_PASSWORD = os.environ['MAIL_PW'],
))
mail = Mail(app)

def is_working(netid):
    groups = get_all_groups()
    for groupid in groups:
        shifts = get_group_schedule(groupid)
        for (key, value) in shifts.items():
            for name in value:
                if name == netid:
                    return True

        shiftsNext = get_group_schedule_next(groupid)
        for (key, value) in shiftsNext.items():
            for name in value:
                if name == netid:
                    return True
    return False

# get shifts netid is working from all shifts scheduled for group
def filter_shifts(netid, shifts):
    newdict = dict()
    for (key, value) in shifts.items():
        #print(key, value)
        for name in value:
            #print("name:", name)
            if name == netid:
                newdict[key] = name
    #print("dict:\n", newdict)
    return newdict


# This function will email every member in a group with their schedule for the next week.
# It will assume that the schedule in groupmembers.userschedule is the one to use
def email_group(groupid, groupName):
    members = get_group_users(groupid)  # get all group members
    shifts = get_group_schedule(groupid)  # group schedule
    if not shifts:
        shifts = {}

    with mail.connect() as conn:
        for netid in members:

            mem_info = get_profile_info(netid)  # get profile info
            if not mem_info.email:  # skips users who have email notifs off
                continue
            sched = filter_shifts(netid, shifts)  # get their weekly schedule
            # sched = shifts_to_us_time(shift)

            output = formatDisplaySched(sched)

            # adds dates to week assuming email is sent on saturday
            html = "<strong>Your shifts this week ({}) are:</strong><br>".format(get_next_week_span())

            for (key, value) in output.items():
                #print(key)
                html += key + "<br>"

            subject = "Your weekly schedule for: %s" % groupName

            msg = Message(subject=subject,
                          html=html,
                          recipients=[mem_info.email],
                          sender='sdylan852@gmail.com')

            conn.send(msg)
    print("Group %s has been emailed" % groupName)
    return


# obtains username
def get_username():
    if PROD_ENV:
        username = CASClient().authenticate()
        username = username.rstrip('\n')
        return username

    else:
        return 'batyas'


# if groupid cookie is set, returns groupid & groupname from cookie
# otherwise if user is in group, returns groupid & groupname that are first on list of user groups
# if user in no group, returns None for both
def getCurrGroupnameAndId(username, request, groups, inGroup=True):
    groupid = request.cookies.get('groupid')
    # if cookie not set, choose first group in user's group list
    if groupid == None and inGroup:
        groupid = groups[0][0]
        groupname = groups[0][1]
    # if group no longer exists, choose first group in list
    elif not group_exists(groupid) and inGroup:
        groupid = groups[0][0]
        groupname = groups[0][1]
    # if group exists but user not in group, choose first group in list
    elif inGroup and not in_group(username, groupid):
        groupid = groups[0][0]
        groupname = groups[0][1]
    elif inGroup:
        groupname = get_group_name(groupid)
    else:
        groupname = None

    return groupname, groupid


# returns bool - is user owner or manager
# (used to display manage group tab in navbar if relevant)
def getIsMgr(username, inGroup, request, groups=None):
    if inGroup:
        if groups == None:
            groups = get_user_groups(username)
        _, groupid = getCurrGroupnameAndId(username, request, groups)
        role = get_user_role(username, groupid)
        if role == -1:
            return role
        return (role in ['manager', 'owner'])
    else:
        return False

# returns bool - is user owner
def getIsOwner(username, inGroup, groupid=None, request=None, groups=None):
    if not inGroup:
        return False
    if inGroup and groupid == None:
        if groups == None:
            groups = get_user_groups(username)
        _, groupid = getCurrGroupnameAndId(username, request, groups)
    role = get_user_role(username, groupid)
    return role == "owner"


# takes a request (schedule element of checkboxes) and returns the schedule values
def parseSchedule():
    table_values = []
    slot_num = 24  # number of time slots in schedule, should be even
    for i in range(slot_num):  # iterates through time slots
        time = i
        week = []
        for day in range(7):  # iterates through days in a week
            if i < (slot_num / 2):
                split = "0"
            else:
                split = "1"
            hour = time % 12
            if hour == 0:
                hour = 12
            str_call = str(hour) + "-" + str(1 + ((time) % 12)) + "-" + str(split) + "-" + str(day)
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


# returns a blank schedule - 24*7 array (array for each hour of day, with slot for each day of week) - all set to False
def blankSchedule():
    return [[False]*7]*24

# convert military time to us time
def military_to_us_time(time):
    if int(time.split(':')[0]) == 0:
        time = "12:00 AM"
    elif int(time.split(':')[0]) < 12:
        time = str(int(time.split(":")[0])) + ":00 AM"
    elif int(time.split(':')[0]) > 12:
        time = str(int(time.split(":")[0]) - 12) + ":00 PM"
    else:
        time = str(int(time.split(":")[0])) + ":00 PM"
    return time

# converts dictionary of shifts to us time
def shiftdict_to_us_time(shifts):
    for i in shifts:
        shifts[i][1] = military_to_us_time(shifts[i][1])
        shifts[i][2] = military_to_us_time(shifts[i][2])
    return shifts

# converts shift key, from "0_0_0" (day of week as int, military starttime, military endtime)
# to "Monday 12:00 AM - 12:00 AM" (day as string, us starttime, us endtime)
def shiftkey_to_str(shiftkey, full=False):
    nums_to_days = {0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday'}
    split = shiftkey.split('_')
    shiftString = "{} {} - {}".format(nums_to_days[int(split[0])], military_to_us_time(split[1]),
                                      military_to_us_time(split[2]))
    return shiftString

# converts shift string to key format ("0_0_0")
def shiftstr_to_key(day, start, end):
    days_to_nums = {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5,
                            'Saturday': 6}
    return "{}_{}_{}".format(days_to_nums[day], start.split(":")[0], end.split(":")[0])

def formatDisplaySched(currsched):
    if currsched:
        keys = sorted(currsched.keys())
        schedStrings = {}
        for key in keys:
            schedStrings[shiftkey_to_str(key)] = currsched[key]
        currsched = schedStrings
    else:
        currsched = None
    return currsched

# returns list of elements in new but not old, and users in old but not new
def getDifferences(newlist, oldlist):
    newElements = []
    lostElements = []
    for element in newlist:
        if element not in oldlist:
            newElements.append(element)
    for element in oldlist:
        if element not in newlist:
            lostElements.append(element)
    return newElements, lostElements


# ------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    isAd = is_admin(username)
    groups = get_user_groups(username)
    numGroups = len(groups)
    inGroup = (numGroups != 0)
    isMgr = getIsMgr(username, inGroup, request, groups)
    isOwner = getIsOwner(username, inGroup, request=request, groups=groups)

    canCreate = can_create_group(username)

    if isMgr == -1: # eg get user role failed
        groupname = groupid = None
    else:
        groupname, groupid = getCurrGroupnameAndId(username, request, groups, inGroup)
    
    if request.method == 'GET':
        html = render_template('index.html', groups=groups, groupid=int(groupid), numGroups=numGroups,
                               inGroup=inGroup, isMgr=isMgr, isOwner=isOwner, isAdmin=isAd, canCreate=canCreate)
        response = make_response(html)
        return response
    # POST request - change group user is viewing site as
    else:
        groupid = request.form.get('groupid')
        role = get_user_role(username, groupid)
        isMgr = (role in ["manager", "owner"])
        isOwner = (role == 'owner')

        html = render_template('index.html', groups=groups, groupid=int(groupid), numGroups=numGroups,
                               inGroup=inGroup, isMgr=isMgr, isOwner=isOwner, isAdmin=isAd, canCreate=canCreate)
        response = make_response(html)
        response.set_cookie('groupid', str(groupid))
        return response

@app.route('/changeNotif', methods=['POST'])
def changeNotifs():
    username = get_username()
    prefemail = request.args.get('prefemail')
    groupid = request.args.get('groupid')
    if prefemail == 'on':
        prefemail = True
    else:
        prefemail = False
    change_group_notifications(groupid, username, prefemail)

# administrator page
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    username = get_username()
    if not (user_exists(username)):
        return redirect(url_for('createProfile'))
    if not is_admin(username):
        return redirect(url_for('index'))

    inGroup = in_any_group(username)
    isMgr = getIsMgr(username, inGroup, request)
    isOwner = getIsOwner(username, inGroup, request=request)

    groups = get_all_groups()
    users = get_all_users()
    admins = []
    isAdmin = {}
    fullNames = {}
    for user in users:
        info = get_profile_info(user)
        fullNames[user] = info[0] + " " + info[1]
        if is_admin(user):
            isAdmin[user] = True
            admins.append(user)
        else:
            isAdmin[user] = False

    # gets admins
    if request.method == "GET":
        html = render_template('admin.html', groups=groups, admins=admins, isAdmin=isAdmin, isMgr=isMgr, 
                               isOwner=isOwner, inGroup=inGroup, users=users,
                               username=username, fullNames=fullNames)
        response = make_response(html)
        return response
    else:
        groupid = request.form.get('groupid')
        if groupid is None:
            groupid = request.cookies.get('adminGroup')
        groupname = get_group_name(groupid)
        curr_members = get_group_users(groupid)
        selected = {}
        isManager = {}
        managers = []
        isGroupOwner = {}
        owners = []
        mgrs = {}
        for user in users:
            selected[user] = False
            if user in curr_members:
                user_role = get_user_role(user, groupid)
                selected[user] = True
            else:
                user_role = "notGroup"

            if user_role == "manager":
                isManager[user] = True
                managers.append(user)
                isGroupOwner[user] = False
            elif user_role == "owner":
                isGroupOwner[user] = True
                owners.append(user)
                isManager[user] = False
            else:
                isManager[user] = False
                isGroupOwner[user] = False

            mgrs[user] = (user_role, (user_role in ['owner', 'manager']))

        # determines input
        output = request.form.get("submit")
        if output == "Save Users":
            selectedUsers = []
            for user in users:
                if request.form.get(user) is not None:
                    selectedUsers.append(user)
            newUsers, oldUsers = getDifferences(selectedUsers, curr_members)

            for user in newUsers:
                add_user_to_group(groupid, user, 'member')
                selected[user] = True
            for user in oldUsers:
                remove_user_from_group(user, groupid)
                selected[user] = False
                mgrs[user] = ("notGroup", False)

            userGroups = get_user_groups(username)
            inGroup = (len(userGroups) != 0)

            html = render_template('admin.html', groups=groups, groupid=int(groupid), groupname=groupname, users=users,
                                   isAdmin=isAdmin, isMgr = isMgr,
                                   selected=selected, mgrs=mgrs, members=selectedUsers, isManager=isManager,
                                   admins=admins, username=username, inGroup=inGroup, isOwner=isOwner, isGroupOwner=isGroupOwner,
                                   fullNames=fullNames)
            response = make_response(html)
            return response
        elif output == "Change Admins":
            selectedAdmins = []
            for user in users:
                if request.form.get(user) is not None:
                    selectedAdmins.append(user)
            selectedAdmins.append(username)
            newAdmins, oldAdmins = getDifferences(selectedAdmins, admins)
            for user in newAdmins:
                change_admin(user, True)
                isAdmin[user] = True
            for user in oldAdmins:
                change_admin(user, False)
                isAdmin[user] = False

            admins = selectedAdmins
            html = render_template('admin.html', groups=groups, admins=admins, isAdmin=isAdmin, inGroup=inGroup, users=users,
                               isMgr=isMgr, isOwner=isOwner, username=username, fullNames=fullNames)
           
            response = make_response(html)
            return response
        elif output == "Save Managers":
            selectedManagers = []
            for member in curr_members:
                if request.form.get(member) is not None:
                    selectedManagers.append(member)

            newManagers, oldManagers = getDifferences(selectedManagers, managers)

            for user in newManagers:
                change_group_role(groupid, user, 'manager')
                isManager[user] = True
                mgrs[user] = ('manager', True)
            for user in oldManagers:
                change_group_role(groupid, user, 'member')
                isManager[user] = False
                mgrs[user] = ('member', False)

            userGroups = get_user_groups(username)
            inGroup = (len(userGroups) != 0)
            
            isMgr = getIsMgr(username, inGroup, request)
            html = render_template('admin.html', groups=groups, groupid=int(groupid), groupname=groupname, users=users,
                                   selected=selected, mgrs=mgrs, members=curr_members, isManager=isManager,
                                   isAdmin=isAdmin, isMgr=isMgr, admins=admins,inGroup=inGroup,  username=username, isOwner=isOwner,isGroupOwner=isGroupOwner,
                                   fullNames=fullNames)
            response = make_response(html)
            return response
        elif output == "Save Owners":
            selectedOwners = []
            for member in curr_members:
                if request.form.get(member) is not None:
                    selectedOwners.append(member)

            newOwners, oldOwners = getDifferences(selectedOwners, owners)

            for user in newOwners:
                change_group_role(groupid, user, 'owner')
                isGroupOwner[user] = True
                isManager[user] = False
                mgrs[user] = ('owner', True)
            for user in oldOwners:
                change_group_role(groupid, user, 'member')
                isGroupOwner[user] = False
                mgrs[user] = ('member', False)
            userGroups = get_user_groups(username)
            inGroup = (len(userGroups) != 0)
            isOwner = getIsOwner(username, inGroup, request=request)
            html = render_template('admin.html', groups=groups, groupid=int(groupid), groupname=groupname, users=users,
                                   selected=selected, mgrs=mgrs, members=curr_members, isManager=isManager,
                                   isAdmin=isAdmin, isMgr=isMgr, admins=admins,inGroup=inGroup,  username=username, isOwner=isOwner,isGroupOwner=isGroupOwner,
                                   fullNames=fullNames)
            response = make_response(html)
            return response
        elif output == "Delete Group":
            remove_group(groupid)
            allGroups = get_all_groups()
            userGroups = get_user_groups(username)
            inGroup = (len(userGroups) > 0)
            if inGroup:
                groupid = userGroups[0][0]
            else:
                groupid = None
            html = render_template('admin.html', groups=allGroups, inGroup=inGroup, admins=admins, isAdmin=isAdmin, isMgr=isMgr, users=users,
                                   isOwner=isOwner, username=username, fullNames=fullNames)
            response = make_response(html)
            response.set_cookie('groupid', str(groupid))
            return response
        elif output == "Delete Users":
            deletedUsers = []
            isOrigOwner = False
            for user in users:
                if request.form.get(user) is not None:
                    if not is_original_owner(user):
                        deletedUsers.append(user)
                    else:
                        isOrigOwner = True
            for user in deletedUsers:
                remove_user(user)
                users.remove(user)
                if user in admins:
                    admins.remove(user)

            html = render_template('admin.html', groups=groups, inGroup=inGroup, admins=admins, isAdmin=isAdmin, isMgr=isMgr,
                                    isOwner=isOwner, users=users, username=username, fullNames=fullNames, isOrigOwner=isOrigOwner)
            response = make_response(html)
            return response
        else:
            html = render_template('admin.html', groups=groups, groupid=int(groupid), groupname=groupname, users=users,
                                   selected=selected, mgrs=mgrs, members=curr_members, isManager=isManager,
                                   isAdmin=isAdmin, isMgr=isMgr, admins=admins, username=username, inGroup=inGroup,  isOwner=isOwner, isGroupOwner=isGroupOwner,
                                   fullNames=fullNames)
            response = make_response(html)
            response.set_cookie('adminGroup', groupid)
            return response


# page for group owners
@app.route('/owner', methods=['GET', 'POST'])
def owner():
    username = get_username()
    if not (user_exists(username)):
        return redirect(url_for('createProfile'))



    isAd = is_admin(username)
    groups = get_user_groups(username)
    if len(groups) == 0:
        return redirect(url_for('index'))
    inGroup = (len(groups) != 0)
    isOwner = getIsOwner(username, inGroup, request=request)
    if not isOwner:
        return redirect(url_for('index'))
    groupname, groupid = getCurrGroupnameAndId(username, request, groups, inGroup)

    users = get_group_users(groupid)
    users.remove(username)
    managers = []
    roles = {}
    isManager = {}
    fullNames = {}
    for user in users:
        info = get_profile_info(user)
        fullNames[user] = info[0] + " " + info[1]
        role = get_user_role(user, groupid)
        roles[user] = role
        if role == "manager":
            isManager[user] = True
            managers.append(user)
        else:
            isManager[user] = False

    if request.method == "GET":
        html = render_template('owner.html', inGroup=inGroup, users=users, isManager=isManager, groupname=groupname,
                               isMgr=True, isOwner=True, isAdmin=isAd, fullNames=fullNames)
        response = make_response(html)
        return response
    else:
        selectedManagers = []
        for user in users:
            if request.form.get(user) is not None:
                selectedManagers.append(user)

        newManagers, removedManagers = getDifferences(selectedManagers, managers)

        for user in newManagers:
            change_group_role(groupid, user, 'manager')
            isManager[user] = True
        for user in removedManagers:
            change_group_role(groupid, user, 'member')
            isManager[user] = False

        html = render_template('owner.html', inGroup=inGroup, users=users, isManager=isManager, groupname=groupname,
                               isMgr=True, isOwner=True, isAdmin=isAd, fullNames=fullNames)
        response = make_response(html)
        return response


@app.route('/profile', methods=['GET'])
def profile():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    isAd = is_admin(username)
    userInfo = get_profile_info(username)
    inGroup = in_any_group(username)
    isMgr = getIsMgr(username, inGroup, request)
    isOwner = getIsOwner(username, inGroup, request=request)

    globalPreferences = blankSchedule()
    try:
        globalPreferences = get_double_array(get_global_preferences(username))
    except Exception:
        pass

    html = render_template('profile.html', firstName=userInfo.firstname, lastName=userInfo.lastname, netid=username,
                           email=userInfo.email,
                           schedule=globalPreferences, inGroup=inGroup, isMgr=isMgr, isOwner=isOwner, editable=False,
                           isAdmin=isAd)

    response = make_response(html)

    return response


@app.route('/manage', methods=['GET', 'POST'])
def manage():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    isAd = is_admin(username)
    groups = get_user_groups(username)

    if len(groups) == 0:
        return redirect(url_for('index'))

    isMgr = getIsMgr(username, True, request, groups)
    if not isMgr:
        return redirect(url_for('index'))

    users = get_all_users()
    users.remove(username)
    groupname, groupid = getCurrGroupnameAndId(username, request, groups, True)
    notGroupInTitle = (not groupname.split()[-1].lower() == 'group')

    curr_members = get_group_users(groupid)
    isOwner = getIsOwner(username, True, groupid)
    selected = {}
    mgrs = {}
    fullNames = {}

    for user in users:
        info = get_profile_info(user)
        fullNames[user] = info[0] + " " + info[1]
        selected[user] = False
        if user in curr_members:
            user_role = get_user_role(user, groupid)
        else:
            user_role = "notGroup"
        mgrs[user] = (user_role, (user_role in ['owner', 'manager']))
    for member in curr_members:
        selected[member] = True

    shifts = get_group_shifts(groupid)
    if not shifts:
        shifts = {}

    thisWeekSpan = get_this_week_span()
    nextWeekSpan = get_next_week_span()

    thisWeekSched = get_group_schedule(groupid)
    thisWeekSched = formatDisplaySched(thisWeekSched)

    nextWeekSched = get_next_group_schedule(groupid)
    nextWeekSched = formatDisplaySched(nextWeekSched)

    draftsched = get_draft_schedule(groupid)
    draftsched = formatDisplaySched(draftsched)

    if request.method == 'GET':
        shifts = shiftdict_to_us_time(shifts)
        html = render_template('manage.html', groupname=groupname, notgroupintitle=notGroupInTitle, inGroup=True, isMgr=isMgr,
                               shifts=shifts, users=users, mgrs=mgrs, selected=selected, thisWeekSpan=thisWeekSpan, nextWeekSpan=nextWeekSpan,
                               thisWeekSched=thisWeekSched, nextWeekSched=nextWeekSched, draftsched = draftsched,
                               username=username, isOwner=isOwner, isAdmin=isAd, fullNames=fullNames)
        response = make_response(html)
        return response

    else:
        publishnotif = generatenotif = errormsg = False
        week = None

        if request.form["submit"] == "Add":

            day = request.form["day"]
            start = request.form["start"]
            end = request.form["end"]
            npeople = request.form["npeople"]

            shift = [day, start, end, npeople]
            shiftid = shiftstr_to_key(day, start, end)
            shifts[shiftid] = shift

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
            for member in curr_members:  # removes users
                remains = False
                for user in n_user_list:
                    if member == user:
                        remains = True
                if not remains:
                    remove_user_from_group(member, groupid)

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
            response.set_cookie('groupid', str(groupid))
            return response
        elif request.form["submit"] == "Generate Schedule":
            try:
                draftsched, preferences, fshifts, memberlist = generate_schedule(groupid)
                conflicts = parse_conflicts(preferences, fshifts, memberlist)
            except:
                draftsched = None
                conflicts = None
                errormsg = True
            if (draftsched == {}):
                for shift in get_group_shifts(groupid):
                    draftsched[shift] = []
                errormsg = True

            # Store schedule, conflicts in DB
            if draftsched is not None:
                change_draft_schedule(groupid, draftsched)
                draftsched = formatDisplaySched(draftsched)
                generatenotif = True
            else:
                draftsched = formatDisplaySched(get_draft_schedule(groupid))
            if conflicts is not None:
                change_group_conflicts(groupid, conflicts)
            else:
                change_group_conflicts(groupid, {})

        elif request.form["submit"] == "Publish draft":
            draftsched = get_draft_schedule(groupid)
            week = request.form["week"]
            if week == "this":
                change_group_schedule(groupid, draftsched)
                # change this week currsched
                thisWeekSched = formatDisplaySched(draftsched)
            if week == "next":
                change_next_group_schedule(groupid, draftsched)
                # reset weekly group prefs of all group members
                groupmems = get_group_members(groupid)
                for mem in groupmems:
                    change_user_preferences_group(groupid, mem)
                nextWeekSched = formatDisplaySched(draftsched)
            # delete draft sched
            change_draft_schedule(groupid, None)
            draftsched = None
            publishnotif = True

        else:
            shiftid = request.form["submit"]
            del shifts[shiftid]
            change_group_shifts(groupid, shifts)
        
        shifts = shiftdict_to_us_time(shifts)
        html = render_template('manage.html', groupname=groupname, inGroup=True, isMgr=isMgr, shifts=shifts,
                               users=users, mgrs=mgrs, selected=selected, thisWeekSpan=thisWeekSpan, nextWeekSpan=nextWeekSpan,
                               thisWeekSched=thisWeekSched, nextWeekSched=nextWeekSched, week=week,
                               publishnotif=publishnotif, generatenotif=generatenotif, errormsg=errormsg, 
                               isOwner=isOwner, username=username, isAdmin=isAd, draftsched=draftsched, fullNames=fullNames)
        response = make_response(html)
        return response


@app.route('/schedule', methods=['GET'])
def schedule():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    isAd = is_admin(username)
    groups = get_user_groups(username)

    if len(groups) == 0:
        return redirect(url_for('index'))

    groupname, groupid = getCurrGroupnameAndId(username, request, groups)
    isMgr = getIsMgr(username, True, request, groups)
    isOwner = getIsOwner(username, True, groupid)

    thisWeekSpan = get_this_week_span()
    nextWeekSpan = get_next_week_span()

    schedule = get_group_schedule(groupid)
    if schedule is not None:
        schedule = get_double_array(parse_user_schedule(username, schedule))

        # check if sched exists but user not scheduled to work at all this week --
        if not any(chain(*schedule)):
            schedule = -1
    
    
    nextWeekSched = get_next_group_schedule(groupid)
    if nextWeekSched is not None:
        nextWeekSched = get_double_array(parse_user_schedule(username, nextWeekSched))

        # check if sched exists but user not scheduled to work at all this week --
        if not any(chain(*nextWeekSched)):
            nextWeekSched = -1
    
    shifts = get_group_shifts(groupid)
    if not shifts:
        shifts = {}
    else:
        shifts = shiftdict_to_us_time(shifts)

    html = render_template('schedule.html', schedule=schedule, withdate=True, thisWeekSpan=thisWeekSpan, nextWeekSpan=nextWeekSpan,
                            dates=get_this_week_array(), nextWeekDates=get_next_week_array(), nextWeekSched=nextWeekSched, groupname=groupname, 
                            shifts=shifts, inGroup=True, isMgr=isMgr, editable=False, isOwner=isOwner, isAdmin=isAd)
    response = make_response(html)

    return response

@app.route('/editdraft', methods=['GET', 'POST'])
def editdraft():

    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    isAd = is_admin(username)
    groups = get_user_groups(username)

    if len(groups) == 0:
        return redirect(url_for('index'))

    isMgr = getIsMgr(username, True, request, groups)
    if not isMgr:
        return redirect(url_for('index'))
    

    
    groupname, groupid = getCurrGroupnameAndId(username, request, groups, True)
    notGroupInTitle = (not groupname.split()[-1].lower() == 'group')
    isOwner = getIsOwner(username, True, groupid)

    groupMembers = get_group_members(groupid)

    raw_schedule = get_draft_schedule(groupid)
    schedule = formatDisplaySched(raw_schedule)

    conflicts = get_group_conflicts(groupid)
    conflicts = formatDisplaySched(conflicts)

    selected = {}
    scheduletype = ""
    if request.method == 'GET':      
        if request.args.get("submit") == "Edit Draft":
            scheduletype = "Draft"
        elif request.args.get("submit") == "Edit This Week":
            scheduletype = "This Week's"
            raw_schedule = get_group_schedule(groupid)
            schedule = formatDisplaySched(raw_schedule)
        elif request.args.get("submit") == "Edit Next Week":
            scheduletype = "Next Week's"
            raw_schedule = get_group_schedule_next(groupid)
            schedule = formatDisplaySched(raw_schedule)

    elif request.method == 'POST':
        if request.form["submit"] == "Save":
            scheduletype = request.form.get('scheduletype')
            rawShift = request.form.get("shift")
            shift = rawShift.split()
            day = shift[0]
            start = shift[1]
            start = start.split(":")
            if shift[2] == 'PM':
                if int(start[0]) != 12:
                    start = str(int(start[0]) + 12) + ":" + start[1]
                else:
                    start = str(int(start[0])) + ":" + start[1]
            elif int(start[0]) < 10:
                start = "0" + start[0] + ":"  + start[1]
            else:
                if(int(start[0])) == 12:
                    start[0] = "00"
                start = start[0] + ":"  + start[1]
            end = shift[4]
            end = end.split(":")

            if shift[5] == 'PM':
                if int(end[0]) != 12:
                    end = str(int(end[0]) + 12) + ":" + end[1]
                else:
                    end = str(int(end[0])) + ":" + end[1]
            elif int(end[0]) < 10:
                end = "0" + end[0] + ":"  + end[1]
            else:
                if(int(end[0])) == 12:
                    end[0] = "00"

                end = end[0] + ":"  + end[1]

            shift = shiftstr_to_key(day, start, end)
            
            selected["shift"] = rawShift

            for member in groupMembers:
                status = request.form.get(member)
                if status is not None:
                    selected[member] = True
                    if scheduletype == "Draft":
                        if member not in raw_schedule[shift]:
                            add_user_to_draft_schedule(groupid, shift, member)

                    elif scheduletype == "This Week's":
                        raw_schedule = get_group_schedule(groupid)
                        schedule = schedule = formatDisplaySched(raw_schedule)
                        if member not in raw_schedule[shift]:
                            add_user_to_shift_schedule(groupid, shift, member)

                    elif scheduletype == "Next Week's":
                        raw_schedule = get_group_schedule_next(groupid)
                        schedule = schedule = formatDisplaySched(raw_schedule)
                        if member not in raw_schedule[shift]:
                            add_user_to_shift_schedule_next(groupid, shift, member)

                    
                else:
                    selected[member] = False
                    if scheduletype == "Draft":
                        if member in raw_schedule[shift]:
                            remove_user_from_draft_schedule(groupid, shift, member)
                    elif scheduletype == "This Week's":
                        raw_schedule = get_group_schedule(groupid)
                        schedule = schedule = formatDisplaySched(raw_schedule)
                        if member in raw_schedule[shift]:
                            remove_user_from_shift_schedule(groupid, shift, member)
                    elif scheduletype == "Next Week's":
                        raw_schedule = get_group_schedule_next(groupid)
                        schedule = schedule = formatDisplaySched(raw_schedule)
                        if member in raw_schedule[shift]:
                            remove_user_from_shift_schedule_next(groupid, shift, member)
                        
    html = render_template('editdraft.html', schedule=schedule, groupname=groupname, inGroup=True, isMgr=isMgr, groupMembers=groupMembers,
                    conflicts=conflicts, shifts=get_group_shifts(groupid), isOwner=isOwner, isAdmin=isAd, notgroupintitle = notGroupInTitle,
                    selected=selected, scheduletype=scheduletype)

    response = make_response(html)
    return response


@app.route('/group', methods=['GET'])
def group():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    isAd = is_admin(username)
    groups = get_user_groups(username)

    if len(groups) == 0:
        return redirect(url_for('index'))

    groupname, groupid = getCurrGroupnameAndId(username, request, groups)
    notGroupInTitle = (not groupname.split()[-1].lower() == 'group')

    isMgr = getIsMgr(username, True, request, groups)
    isOwner = getIsOwner(username, True, groupid)
    groupprefs = get_group_preferences(groupid, username)
    if groupprefs == None:
        change_user_preferences_global(username, create_preferences(blankSchedule()))
        groupprefs = get_global_preferences(username)
    weeklyPref = get_double_array(groupprefs)

    notifPrefs = get_group_notifications(username, groupid)
    if notifPrefs != None and notifPrefs != -1:
        prevemailPref = notifPrefs.emailnotif
    else:
        prevemailPref = False

    html = render_template('group.html', schedule=weeklyPref, groupname=groupname, prevemailPref=prevemailPref,
                           inGroup=True, isMgr=isMgr, notgroupintitle=notGroupInTitle, isOwner=isOwner, editable=False,
                           isAdmin=isAd)
    response = make_response(html)
    return response


@app.route('/editGroup', methods=['GET', 'POST'])
def editGroup():
    username = get_username()

    if not (user_exists(username)):
        return redirect(url_for('createProfile'))

    isAd = is_admin(username)
    groups = get_user_groups(username)

    if len(groups) == 0:
        return redirect(url_for('index'))

    groupname, groupid = getCurrGroupnameAndId(username, request, groups)
    notGroupInTitle = (not groupname.split()[-1].lower() == 'group')
    isMgr = getIsMgr(username, True, request, groups)
    isOwner = getIsOwner(username, True, groupid)

    groupprefs = get_group_preferences(groupid, username)
    if groupprefs == None:
        change_user_preferences_global(username, create_preferences(blankSchedule()))
        groupprefs = get_global_preferences(username)
    weeklyPref = get_double_array(groupprefs)

    prevemailPref = get_group_notifications(username, groupid).emailnotif

    if request.method == 'GET':
        html = render_template('editGroup.html', schedule=weeklyPref, groupname=groupname, prevemailPref=prevemailPref,
                               inGroup=True, isMgr=isMgr, isOwner=isOwner, notgroupintitle=notGroupInTitle,
                               editable=True, isAdmin=isAd)
        response = make_response(html)
        return response
    

@app.route('/viewGroup', methods=['GET'])
def viewGroup():
    username = get_username()
    inGroup = in_any_group(username)
    isAd = is_admin(username)
    if not inGroup:
        return redirect(url_for('index'))
    groups = get_user_groups(username)
    isMgr = getIsMgr(username, True, request, groups)
    gName, groupId = getCurrGroupnameAndId(username, request, groups)
    notGroupInTitle = (not gName.split()[-1].lower() == 'group')

    isOwner = getIsOwner(username, True, groupId)

    members = get_group_users(groupId)
    fullNames = {}
    for member in members:
        info = get_profile_info(member)
        fullNames[member] = info[0] + " " + info[1]

    members_w_roles = [(member, get_user_role(member, groupId)) for member in members]
    html = render_template('viewGroup.html', gName=gName, notgroupintitle=notGroupInTitle, members=members_w_roles,
                           inGroup=True, isMgr=isMgr, isOwner=isOwner, isAdmin=isAd, fullNames=fullNames)
    response = make_response(html)

    return response


@app.route('/createGroup', methods=['GET', 'POST'])
def createGroup():
    username = get_username()

    isAd = is_admin(username)
    inGroup = in_any_group(username)
    isMgr = getIsMgr(username, inGroup, request)
    isOwner = getIsOwner(username, inGroup, request=request)

    names = get_all_users()
    try:
        names.remove(username)
    except:  # remove method errors if element not within
        ()

    fullNames = {}
    for name in names:
        info = get_profile_info(name)
        fullNames[name] = info[0] + " " + info[1]

    currUserInfo = get_profile_info(username)
    nameOfUser = currUserInfo[0] + " " + currUserInfo[1]

    if request.method == 'GET':
        html = render_template('createGroup.html', names=names, inGroup=inGroup, isMgr=isMgr, isOwner=isOwner,
                               isAdmin=isAd, username=username, nameOfUser=nameOfUser, fullNames=fullNames)
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
        html = render_template('createProfile.html', schedule=blankSchedule(), inGroup=False, isMgr=False,
                               isOwner=False, editable=True, isAdmin=False)
        response = make_response(html)
        return response

    else:
        fname = request.form['fname']
        lname = request.form['lname']

        email = request.form['email']

        # notification preferences default to false 
        prefemail = False

        globalPreferences = parseSchedule()

        if not (user_exists(username)):
            add_user(fname, lname, username, email, create_preferences(globalPreferences))
        else:
            update_profile_info(fname, lname, username, email, create_preferences(globalPreferences))

        return redirect(url_for('profile'))


@app.route('/editProfile', methods=['GET', 'POST'])
def editProfile():
    username = get_username()

    isAd = is_admin(username)
    inGroup = in_any_group(username)
    isMgr = getIsMgr(username, inGroup, request)
    isOwner = getIsOwner(username, inGroup, request=request)
    userInfo = get_profile_info(username)
    prevfirstName = userInfo.firstname
    prevlastName = userInfo.lastname
    prevemail = userInfo.email

    prevGlobalPreferences = blankSchedule()
    try:
        prevGlobalPreferences = get_double_array(get_global_preferences(username))
    except Exception:
        pass

    if request.method == 'GET':
        html = render_template('editProfile.html', prevfname=prevfirstName, prevlname=prevlastName,
                               prevemail=prevemail, schedule=prevGlobalPreferences, inGroup=inGroup, isMgr=isMgr,
                               isOwner=isOwner, editable=True, isAdmin=isAd)
        response = make_response(html)
        return response

    else:
        if request.form["submit"] == "Save Information":
            fname = request.form['fname']
            lname = request.form['lname']
            email = request.form['email']

            update_profile_info(fname, lname, username, email, create_preferences(prevGlobalPreferences))

        if request.form["submit"] == "Save Preferences":
            globalPreferences = parseSchedule()

            update_profile_info(prevfirstName, prevlastName, username, prevemail, create_preferences(globalPreferences))

        return redirect(url_for('profile'))

app.add_url_rule('/favicon.ico',
                 redirect_to=url_for('static', filename='favicon.ico'))

if __name__ == '__main__':
    app.run()
