import json
import requests
from config import *
from flask import (
    render_template,
    redirect,
    request,
    url_for,
    session,
    flash,
)
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from flask.ext.login import login_user, logout_user, current_user
from flask.ext.oauth import OAuth
from wikimetrics.web import app, login_manager, is_public
from wikimetrics.database import get_session
from wikimetrics.models import User, UserRole


oauth = OAuth()
google = oauth.remote_app(
    'google',
    base_url=GOOGLE_BASE_URL,
    authorize_url=GOOGLE_AUTH_URI,
    request_token_url=None,
    request_token_params={
        'scope': GOOGLE_AUTH_SCOPE,
        'response_type': 'code',
    },
    access_token_url=GOOGLE_TOKEN_URI,
    access_token_method='POST',
    access_token_params={
        'grant_type':
        'authorization_code'
    },
    consumer_key=GOOGLE_CLIENT_ID,
    consumer_secret=GOOGLE_CLIENT_SECRET,
)


@login_manager.user_loader
def load_user(user_id):
    """
    Callback required by Flask-Login.  Gets the User object from the database.
    """
    db = get_session()
    user = User.get(db, user_id)
    return user


@login_manager.unauthorized_handler
@app.route('/login')
@is_public
def login():
    """
    Render authentication options.
    """
    session['next'] = request.args.get('next') or request.referrer or None
    return render_template('authenticate.html')


@app.route('/logout')
@is_public
def logout():
    """
    Logs out the user.
    """
    db = get_session()
    current_user.logout(db)
    logout_user()
    return redirect(url_for('home_index'))


@app.route('/login/google')
@is_public
def login_google():
    """
    Make a request to Google for Authentication.
    """
    auth_callback = url_for('auth_google', _external=True)
    return google.authorize(callback=auth_callback)


@app.route('/auth/google')
@google.authorized_handler
@is_public
def auth_google(resp):
    """
    Callback for Google to send us authentication results.
    This is responsible for fetching existing users or creating new ones.
    If a new user is created, they get the default role of GUEST and
    an email or username to match their details from the OAuth provider.
    """
    access_token = resp['access_token'] or request.args.get('code')
    if access_token:
        # TODO: is it better to store this in the database?
        session['access_token'] = access_token, ''
        r = requests.get(GOOGLE_USERINFO_URI, headers={
            'Authorization': 'OAuth ' + access_token
        })
        if r.ok:
            userinfo = json.loads(r.text)
            email = userinfo['email']
            id = userinfo['id']
            
            db = get_session()
            user = None
            try:
                user = db.query(User).filter_by(google_id = id).one()
            
            except NoResultFound:
                user = User(
                    email=email,
                    google_id=id,
                    role=UserRole.GUEST,
                )
                db.add(user)
                db.commit()
            
            except MultipleResultsFound:
                return 'Multiple users found with your id!!! Contact Administrator'
            
            user.login(db)
            if login_user(user):
                user.detach_from(db)
                redirect_to = session.get('next') or url_for('home_index')
                return redirect(redirect_to)
    
    flash('Was not allowed to authenticate you with Google.', 'error')
    return redirect(url_for('login'))


@google.tokengetter
def get_access_token():
    return session.get('access_token')


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
