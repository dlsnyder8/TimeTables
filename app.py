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
    html = render_template('profile.html')
    response = make_response(html)

    return response



@app.route('/schedule', methods=['GET'])
def schedule():
    html = render_template('schedule.html')
    response = make_response(html)

    return response

@app.route('/groupInfo', methods=['GET'])
def groupInfo():
    html = render_template('groupInfo.html')
    response = make_response(html)

    return response


@app.route('/createProfile',methods=['GET'])
def createProfile():
    html = render_template('setupProfile.html')
    response = make_response(html)

    return response


if __name__ == '__main__':
    app.run()
