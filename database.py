# Has interface for the database
#-----------------
# imports
import os
from sys import stderr, exit
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session, create_session, Session
from sqlalchemy.ext.automap import automap_base
#-------------------

DATABASE_URL = os.environ['DATABASE_URL']

# create engine (db object basically)
engine = create_engine(DATABASE_URL)
#start automap and create session with automap
Base = automap_base()
Base.prepare(engine, reflect=True)

session = Session(engine)

users = Base.classes.users
groups = Base.classes.groups
group_members = Base.classes.groupmembers


# adds a user to the database
def add_user(firstName, lastName, netid, email, phone, preferences):
    return


# removes a user from a group
def remove_user(netid, groupid):
    return


#replaces the personal preferences of a user, global
def change_user_preferences_global(netid, preferences):
    return


# replaces weekly preferences of user. If none specified, 
# replaces it with global preferences
def change_user_preferences_group(groupid, netid, preferences = None):
    return

# Adds a group, shiftSchedule is optional argument if known
# should call add_user_to_group with owner role
def add_group(owner, groupName, shiftSchedule = None):
    return



# removes a group
def remove_group(groupid):
    return


# Replaces the schedule of the group specified by groupid
def change_group_schedule(groupid, schedule):
    return

# add a user (netid) to group (groupid), 
# preferences is optional argument, but could default to global if None???
# valid options for 'role' are: 'manager', 'owner', 'member'
def add_user_to_group(groupid, netid, role, preferences = None):
    return

# changes the role of a person (netid) in a group (groupid) to 'role'
def change_group_role(groupid, netid, role):
    return

# change the notifications of a person in a group
# email and text should always be specified when calling this function
def change_group_notifications(groupid, netid, emailnotif = False, textnotif = False):
    return