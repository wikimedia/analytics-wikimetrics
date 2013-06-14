from flask import render_template, redirect, request
from flask_login import login_user
from wikimetrics.web import app, login_manager
from wikimetrics.database import get_session
from config_secret import *


@login_manager.unauthorized_handler
@app.route('/login')
def login():
    return render_template('authenticate.html')


@login_manager.user_loader
def load_user(user_id):
    return None


@app.route('/login/google')
def login_google():
    return redirect(GOOGLE_AUTH_URI)


@app.route('/login/twitter')
def login_twitter():
    return redirect(TWITTER_AUTH_URI)
