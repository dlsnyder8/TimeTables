# TimeTables

Authors: Dylan Snyder, Bates Brodie, Batya Stein, Kevin Zheng, and AJ Kawczynski



To run this app you should:

Create a python environment for this project. If you have a env/ folder already in your directory, delete it and make another folder also called env/.
$ python3 -m venv env


You should then activate the venv (same thing you do for the assignments) and run this command:
$ pip install -r requirements.txt

This will ensure that we are all running the same versions of packages

Install autoenv (it will automatically run an .env files when you cd into a directory)
Mac -   $ brew install autoenv
        $ echo "source $(brew --prefix autoenv)/activate.sh" >> ~/.bash_profile

Pip (linux) -  $ pip install autoenv
               $ echo "source `which activate.sh`" >> ~/.bashrc 

If you use windows, I couldn't figure out how to do this. You can activate the python environment how you normally do, but I think you'll have to do more work to export the PostgreSQL login to your environment variables.

The only other thing you will have to do is create a Heroku login so that you can access the db locally and also run the code locally to test. As of writing this, I have requested that you all create one and send me the email so it shouldn't be an issue.

The only command you need to know for heroku (I think) is:
$ heroku local








About: Time Tables is a employee scheduling application for use by Princeton University Staff and Students through CAS authentication.

Features include: 

Inviting and managing employees

Shift creation 

Automatic scheduling at the click of a button

Employees can add preferences for hours that they want to work, cannot work, or would prefer not to work

Employees can request days off

Text/Email notifications when the schedule is posted

Simple Web UI that is easy to navigate

