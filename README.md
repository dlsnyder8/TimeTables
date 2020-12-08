# TimeTables

Authors: Dylan Snyder, Bates Brodie, Batya Stein, Kevin Zheng, and AJ Kawczynski

## About: Time Tables is a employee scheduling application for use by Princeton University Staff and Students through CAS authentication.

Time Tables is a employee shift scheduling and management application for use by Princeton University student organizations. It was inspired in particular by Coffee Club, a group which was suffering from high enterprise shift management software costs.

Features include:

- Automatic scheduling at the click of a button, algorithmically generated through a modified version Google OR tools' scheduling alogrithm

- Multiple groups can be created for various sections of the company, each with distinct managers and users, and its own weekly schedule

- Employees can input global and weekly availibilty to determine when they will be scheduled

- Email notifications when the week's schedule is posted

- Front-end administrator panel to modify and delete system groups and users

- Simple Web UI that is easy to navigate

## Architecture 


## How to Run

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

