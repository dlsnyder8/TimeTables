from shift import solve_shift_scheduling
from database import *

def create_requests(pshifts, prefArray, employeeNum, currentPrefs):
    shiftNum = 1
    for key in pshifts:
        items = key.split('_')
        start = items[0]
        end = items[1]
        # check each day for any given shift
        for i in range(len(pshifts[key])):
            if pshifts[key][i] != 0:
                for j in range(int(start), int(end)):
                    if prefArray[j][i] == False:
                        currentPrefs.append((employeeNum, shiftNum, i, 10000))
                        break
        shiftNum += 1

    return currentPrefs


# parse shifts from get_group_shifts in database
def parse_shifts(shifts):
    output = {}
    for key in shifts:
        items = key.split('_')
        day = items[0]
        day = int(day)
        start = items[1]
        end = items[2]
        shift = start + "_" + end
        if not shift in output:
            output[shift] = [0] * 7 
        output[shift][day] = int(shifts[key][3])
    return output

# gets algorithm output ready for DB
def format_schedule(edict, memberlist):
    output = {}
    for key in edict:
        week = edict[key]
        for i in range(len(week)):
            if week[i] != 'O':
                newshift = str(i) + "_" + week[i]
                if newshift not in output:
                    output[newshift] = []
                output[newshift].append(memberlist[key])
    return output

def cover_demands(pshifts):
    output  = []
    i = 0
    for key in pshifts:
        for j in range(7):
            if i == 0:
                output.append([])
            output[j].append(pshifts[key][j])
        i += 1
    return output

# This generates a schedule based on groupID!
# returns an empty dict {} if no solution found
# otherwise, just call generate schedule to put it in database +
# parse schedule for each netid
def generate_schedule(groupid):
    shifts = get_group_shifts(groupid)
    pshifts  = parse_shifts(shifts)

    fshifts = ['O']
    fshifts += list(pshifts.keys())

    weekly_cover_demands = cover_demands(pshifts)

    memberlist = get_group_members(groupid)
    prefs = []
    i = 0
    for member in memberlist:
        prefs = create_requests(pshifts, get_double_array(get_group_preferences(groupid, member)), i, prefs)
        i+= 1  
    edict = solve_shift_scheduling("", "", len(memberlist), 1, fshifts, [], prefs, weekly_cover_demands)
    return format_schedule(edict, memberlist), prefs, fshifts, memberlist

# Parses conflicts
def parse_conflicts(prefs, fshifts, memberlist):
    conflicts = {}
    for preference in prefs:
        keystring = str(preference[2]) + "_" + fshifts[preference[1]]
        netid = memberlist[preference[0]]
          
        if keystring not in conflicts:
            conflicts[keystring] = []
        conflicts[keystring].append(netid)
    return conflicts
        
def main():
    schedule, prefs, fshifts, memberlist = generate_schedule(81)
    change_group_schedule(81, schedule)
    print(parse_conflicts(prefs, fshifts, memberlist))
    
    

if __name__ == '__main__':
    main()