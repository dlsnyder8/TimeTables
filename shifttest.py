from shift import solve_shift_scheduling

def create_requests(prefArray, employeeNum):
    offshifts = []
    
    for i in range(len(prefArray)):
        hourArray = prefArray[i]
        for j in range(len(hourArray)):
            shiftNum = 0
            if hourArray[j] == False:
                if i < 8:
                    shiftNum = 0
                elif i < 11:
                    shiftNum = 1
                elif i < 14:
                    shiftNum = 2
                elif i < 17:
                    shiftNum = 3
                if shiftNum != 0:
                    addTuple = (employeeNum, shiftNum, j, 100)
                    if addTuple not in offshifts:
                        offshifts.append((employeeNum, shiftNum, j, 100))
    return offshifts

def create_schedule(edict, employeeNum):
    outputlist = [[False] * 7] * 8
    for i in range(3):
        newlistrow = []
        for j in range(7):
            if (edict[employeeNum][j] == 'M'):
                newlistrow.append(True)
            else:
                newlistrow.append(False)
        outputlist.append(newlistrow)
    for i in range(3):
        newlistrow = []
        for j in range(7):
            if (edict[employeeNum][j] == 'A'):
                newlistrow.append(True)
            else:
                newlistrow.append(False)
        outputlist.append(newlistrow)
    for i in range(3):
        newlistrow = []
        for j in range(7):
            if (edict[employeeNum][j] == 'N'):
                newlistrow.append(True)
            else:
                newlistrow.append(False)
        outputlist.append(newlistrow)
    for i in range(7):
        outputlist.append([False] * 7)
    return outputlist
   
        
def main():
    prefArray = [[False, False, True, False, False, False, False], 
    [False, False, True, False, False, False, False], 
    [False, False, True, False, False, False, False], 
    [False, False, True, False, False, False, False], 
    [False, False, True, False, False, False, False], 
    [False, False, False, False, False, False, False], 
    [False, False, False, False, False, False, False], 
    [False, False, False, False, False, False, False], 
    [True, False, False, False, False, False, False],
    [True, False, False, False, False, False, False], 
    [True, False, False, False, False, False, False], 
    [True, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False], [False, False, False, False, False, False, False]]
    edict = solve_shift_scheduling("", "", 10, 1, ['O', 'M', 'A', 'N'], [], create_requests(prefArray, 0))
    
    print(create_schedule(edict, 0))
    

if __name__ == '__main__':
    main()