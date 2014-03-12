#!/usr/bin/env python
"""
HiveFeed
Developed by Trevor Stanhope
Mobile web-app Flask server for monitoring distributed hives hive monitors.

TODO:
- update firebase log on tweet
- proper redirect on tweet
"""
# Constants
FLASK_IP = '0.0.0.0'
FLASK_PORT = 5000
FIREBASE = 'hivemind'
FIREBASE_ADDR = 'https://' + FIREBASE + '.firebaseio.com'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'
DEBUG = True

# Libraries
import json
from flask import Flask, url_for, render_template, request, redirect, session, flash
from flask_oauth import OAuth
from pymongo import MongoClient
import datetime

# API Keys
with open('api_keys.json', 'r') as keyfile:
    keys = json.loads(keyfile.read())
    FLASK_SECRET = keys['FLASK_SECRET']
    TWITTER_KEY = keys['TWITTER_KEY']
    TWITTER_SECRET = keys['TWITTER_SECRET']

# Global Objects
app = Flask(__name__)
app.secret_key = FLASK_SECRET
oauth = OAuth()
twitter = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1.1/', #API_V1.1
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authorize',
    consumer_key=TWITTER_KEY,
    consumer_secret=TWITTER_SECRET
)

# Twitter Session
@twitter.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')

# Index
@app.route('/')
def index():
    return render_template('index.html')

# Login 
@app.route('/login')
def login():
    if session.has_key('twitter_token'):
        del session['twitter_token']
    return twitter.authorize(callback=url_for('oauth_authorized',
        next=(request.args.get('next') or request.referrer or None)))

# Logout 
@app.route('/logout')
def logout():
    if session.has_key('twitter_token'):
        del session['twitter_token']
    return redirect(url_for('index'))

# OAuth
@app.route('/oauth_authorized')
@twitter.authorized_handler
def oauth_authorized(resp):
    if resp is None:
        return redirect(url_for('index')) #BADLOGIN
    else:
        session['twitter_token'] = (
            resp['oauth_token'],
            resp['oauth_token_secret']
        )
        session['twitter_user'] = resp['screen_name']
        return redirect('/user/' + session['twitter_user'])

# User
@app.route('/user/<username>')
def user(username):
    return render_template('user.html',
        username=username,
    )

# Tweet
@app.route('/tweet', methods=['POST'])
def tweet():
    if not session.has_key('twitter_token'):
        return redirect(url_for('login', next=request.url))
    log = request.form['log'] # get ?log= from the post request
    if not log:
        return redirect('/user/' + session['twitter_user']) # refresh page if empty form entered
    resp = twitter.post('statuses/update.json', data={
        'status':log # %23 is for hash tags
    })
    if resp.status == 403:
        print(str(resp.status) + ': Your tweet was too long.')
    elif resp.status == 401:
        print(str(resp.status) + ': Authorization error with Twitter.')
    elif resp.status == 410:
        print(str(resp.status) + ': Resource not found.')
    else:
        print(str(resp.status) + ': Other')
    return redirect('/user/' + session['twitter_user'])

# Aggregator
@app.route('/aggregator/<aggregator>')
def aggregator(aggregator):
    return render_template('aggregator.html',
	    aggregator=aggregator,
    )

# Hive
@app.route('/hive/<hive>')
def hive(hive):
    return render_template('hive.html',
	    hive=hive,
    )

# Sample
@app.route('/sample/<sample>')
def sample(sample):
    return render_template('sample.html',
	    sample=sample,
    )

# Log
@app.route('/log/<log>')
def log(log):
    return render_template('log.html',
	    log=log,
    )

# 404
@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

# Run Server
if __name__ == '__main__':
    app.run(FLASK_IP, port=FLASK_PORT, debug=DEBUG)
