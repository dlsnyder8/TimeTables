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

# call this function on the preferences array
def create_preferences(hoursList):
    output = {}
    for i in range(len(hoursList)):
        output[i] = hoursList[i]
    return output

# dict to double array
def get_double_array(preferences):
    output = []
    for i in range(len(preferences)):
        output.append(preferences[str(i)])
    return output

# adds a user to the database
def add_user(firstName, lastName, netid, email=None, phone=None, preferences=None):
    session.add(Users(firstname=firstName,lastname=lastName,netid=netid,email=email,phone=phone,globalpreferences=preferences))
    session.commit()
    return

def user_exists(netid):
    return session.query(Users).filter(Users.netid == netid).scalar() is not None
    
# removes a user from a group
def remove_user(netid, groupid):
    session.delete(Users(netid=netid))
    session.commit()
    return


#replaces the personal preferences of a user, global
def change_user_preferences_global(netid, preferences):
    session.add(Users(netid=netid, globalpreferences=preferences))
    session.commit()
    return

# this could break if we change database row names!
def get_global_preferences(netid):
    pref = session.query(Users.globalpreferences).filter_by(netid=netid).first()

    return pref._asdict()['globalpreferences']


# replaces weekly preferences of user. If none specified, 
# replaces it with global preferences
def change_user_preferences_group(groupid, netid, preferences = None):
    if(preferences==None):
       preferences = get_global_preferences
       # preferences = get_global_preferences(netid) ?
    
    userid = get_user_id(groupid,netid)
    session.add(Group_members(inc=userid, grouppreferences = preferences))
    session.commit()
    return

#used in above function to access primary key
def get_user_id(groupid,netid):
    userid = session.query(Group_members.inc).filter_by(groupid=groupid,netid=netid).first()
    # there's no inc key in users table?
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

# retrieve name, email, phone from user table & notif prefs from group table
def get_profile_info(netid, groupid):
    userInfo = session.query(Users.firstname, Users.lastname, Users.email, Users.phone).filter_by(netid=netid).first()
    notifPrefs = session.query(Group_members.emailnotif, Group_members.textnotif).filter_by(netid=netid, groupid=groupid).first()
    return userInfo, notifPrefs


# adds a user to the database
def update_user(firstName, lastName, netid, email=None, phone=None, textPref=False, emailPref=False, preferences=None):
    session.query(Users).filter_by(netid=netid).update({Users.firstname : firstName, Users.lastname: lastName, Users.email: email, Users.phone: phone, Users.globalpreferences: preferences})
    session.query(Group_members).filter_by(netid=netid).update({Group_members.emailnotif: emailPref, Group_members.textnotif: textPref})

    session.commit()
    return


if __name__=="__main__":
    # test
    # add_user('batya','stein','batyas',email='batyas@princeton.edu',phone='7327660532')
    #add_user_to_group(1, 'batyas','member')

    update_user('test', 'user', 'test123', email = 'test@test.com', emailPref = True, preferences=create_preferences([[1,2],[1,2]]))
    print(user_exists('test2'))

