# Has interface for the database
#-----------------
# imports
import os
from sys import stderr, exit
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session, create_session, Session
from sqlalchemy.ext.automap import automap_base
#-------------------
# CAS Authentication cannot be run locally unfortunately
# Set this variable to 1 if local, and change to 0 before pushing
LOCAL_ENV = 0




#----------
DATABASE_URL = os.environ['DATABASE_URL']

# create engine (db object basically)
engine = create_engine(DATABASE_URL)
#start automap and create session with automap
Base = automap_base()
Base.prepare(engine, reflect=True)

session = Session(engine)

Users = Base.classes.users
Groups = Base.classes.groups
Group_members = Base.classes.groupmembers


# adds a user to the database
def add_user(firstName, lastName, netid, email=None, phone=None, preferences=None):
    session.add(Users(firstname=firstName,lastname=lastName,netid=netid,email=email,phone=phone,global_preferences=preferences))
    session.commit()
    return


# removes a user from a group
def remove_user(netid, groupid):
    session.delete(Users(netid=netid))
    session.commit()
    return


#replaces the personal preferences of a user, global
def change_user_preferences_global(netid, preferences):
    session.add(Users(netid=netid, global_preferences=preferences))
    session.commit()
    return

def get_global_preferences(netid):
    pref = session.query(Users.global_preferences).filter_by(netid=netid).first()
    return pref 

# replaces weekly preferences of user. If none specified, 
# replaces it with global preferences
def change_user_preferences_group(groupid, netid, preferences = None):
    if(preferences==None):
       preferences = get_global_preferences

    
    userid = get_user_id(groupid,netid)
    session.add(Group_members(inc=userid, grouppreferences = preferences))
    session.commit()
    return

#used in above function to access primary key
def get_user_id(groupid,netid):
    userid = session.query(Users.inc).filter_by(groupid=groupid,netid=netid).first()
    return userid

# Adds a group, shiftSchedule is optional argument if known
# should call add_user_to_group with owner role
def add_group(owner, groupName, shiftSchedule = None):
    statement = Groups(owner=owner, groupname=groupName,shiftSchedule=shiftSchedule)
    session.add(statement)
    session.flush()
    groupid=statement.groupid
    add_user_to_group(groupid,owner,'owner')
    session.commit()
    return



# removes a group
def remove_group(groupid):
    session.delete(Groups(grouid=groupid))
    session.commit()
    return


# Replaces the schedule of the group specified by groupid
def change_group_schedule(groupid, schedule):
    session.add(Groups(groupid=groupid, shiftSchedule=schedule))
    session.commit()
    return

# add a user (netid) to group (groupid), 
# preferences is optional argument, but could default to global if None???
# valid options for 'role' are: 'manager', 'owner', 'member'
def add_user_to_group(groupid, netid, role, email=False,text=False,preferences = None):
    session.add(Group_members(netid=netid,groupid=groupid,role=role,emailnotif=email,textnotif=text,grouppreferences=preferences))
    session.commit()
    return

# changes the role of a person (netid) in a group (groupid) to 'role'
def change_group_role(groupid, netid, role):
    userid=get_user_id(groupid,netid)
    session.add(Group_members(inc=userid,role=role))
    session.commit()
    return

# change the notifications of a person in a group
# email and text should always be specified when calling this function
def change_group_notifications(groupid, netid, emailnotif = False, textnotif = False):
    userid=get_user_id(groupid,netid)
    session.add(Group_members(inc=userid,emailnotif=emailnotif,textnotif=textnotif))
    session.commit()
    return