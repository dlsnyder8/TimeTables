# used to grab database URL from heroku for testing. Must redirect this file to .env
# ./update.sh > .env


echo "source env/bin/activate"
printf "%s%s" "DATABASE_URL=" "$(heroku config:get DATABASE_URL -a timetables1)"