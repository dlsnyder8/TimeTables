from database import get_all_groups,get_group_schedule_next,change_group_schedule, change_group_schedule_next
import datetime
def main():
    # because the scheduler runs daily (heroku limitation)
    # we have to check if the current day is saturday
    if datetime.datetime.today().weekday() is 5:

        groups = get_all_groups()

        # For each group, get the schedule for next week, set the next week schedule to None,
        # and change the current week's schedule to next weeks

        # TODO: Add saving of the old schedule into here
        for groupid in groups:
            nextSched = get_group_schedule_next(groupid)
            change_group_schedule_next(groupid, None)

            change_group_schedule(groupid, nextSched)


            # Save this weeks schedule 

        



if __name__ == "__main__":
    main()