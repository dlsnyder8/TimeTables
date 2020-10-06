from flask import Flask
from flask import render_template, make_response, request, redirect, url_for
from CASClient import CASClient


app = Flask(__name__)


@app.route('/',methods=['GET'])
@app.route('/index',methods=['GET'])
def index():
    
    html = render_template('index.html')
    response = make_response(html)

    return response



@app.route('/profile',methods=['GET'])
def profile():
    return "profile page"



@app.route('/schedule', methods=['GET'])
def schedule():
    return "schedule page"

@app.route('/groupInfo', methods=['GET'])
def groupInfo():
    return "Group info"


@app.route('/createProfile',methods=['GET'])
def createProfile():
    return "Create Profile Page"


if __name__ == '__main__':
    app.run()
