import datetime

def get_weekday(d, weekday, add = 0):
    days_ahead = weekday - d.weekday()
    return d + datetime.timedelta(days_ahead + add) 

# returns array of this week and next week's dates, in format "month. day" (ex. Dec. 01)
def get_dates_array():
    today = datetime.date.today() 
    dates = []
    if today.weekday() == 6:
        dates = [get_weekday(today, i, 6).strftime("%b. %d") for i in range(14)]
    else:
        dates = [get_weekday(today, i, -1).strftime("%b. %d") for i in range(14)]
    return dates

def get_this_week_array():
    today = datetime.date.today() 
    dates = []
    if today.weekday() == 6:
        dates = [get_weekday(today, i, 6).strftime("%b. %d") for i in range(7)]
    else:
        dates = [get_weekday(today, i, -1).strftime("%b. %d") for i in range(7)]
    return dates

def get_next_week_array():
    today = datetime.date.today() 
    dates = []
    if today.weekday() == 6:
        dates = [get_weekday(today, i, 13).strftime("%b. %d") for i in range(7)]
    else:
        dates = [get_weekday(today, i, 6).strftime("%b. %d") for i in range(7)]
    return dates

def get_this_week_span():
    dates = get_this_week_array()
    return "{} - {}".format(dates[0], dates[6])

def get_next_week_span():
    dates = get_next_week_array()
    return "{} - {}".format(dates[0], dates[6])

if __name__ == '__main__':
    dates = get_next_week_array()
    print(dates)
    print(get_this_week_span())

