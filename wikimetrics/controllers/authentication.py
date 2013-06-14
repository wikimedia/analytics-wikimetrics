import json
from flask import render_template, redirect, request, url_for
from flask.ext.login import login_user
from wikimetrics.web import app, login_manager, is_public
from wikimetrics.database import get_session
from wikimetrics.models import User
from config import *
from rauth import OAuth2Service


google_service = OAuth2Service(
    client_id = GOOGLE_CLIENT_ID,
    client_secret = GOOGLE_CLIENT_SECRET,
    name = 'google_service',
    authorize_url = GOOGLE_AUTH_URI,
    access_token_url = GOOGLE_TOKEN_URI,
)

@login_manager.user_loader
def load_user(user_id):
    """
    Callback required by Flask-Login.  Gets the User object from the database.
    """
    session = get_session()
    user = User.get(session, user_id)


@login_manager.unauthorized_handler
@app.route('/login')
@is_public
def login():
    """
    Render authentication options.
    """
    return render_template('authenticate.html')


@app.route('/login/google')
@is_public
def login_google():
    """
    Make a request to Google for Authentication.
    """
    params = {
        'response_type': 'code',
        'scope': GOOGLE_AUTH_SCOPE,
        'redirect_uri': GOOGLE_REDIRECT_URI,
    }
    google_auth_url = google_service.get_authorize_url(**params)
    return redirect(google_auth_url)


@app.route('/auth/google')
@is_public
def auth_google():
    """
    Callback for Google to send us authentication results.
    """
    return request.args['code']


@app.route('/login/twitter')
@is_public
def login_twitter():
    """
    Make a request to Twitter for Authentication.
    """
    return 'Not Implemented Yet'


@app.route('/auth/twitter')
@is_public
def auth_twitter():
    """
    Callback for Twitter to send us authentication results.
    """
    return 'Not Implemented Yet'
