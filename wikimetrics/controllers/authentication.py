import json
import requests
import urllib2
import jwt
import time
import traceback
from flask import (
    render_template,
    redirect,
    request,
    url_for,
    session,
    flash,
)
from mwoauth import Handshaker, RequestToken
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from flask.ext.login import login_user, logout_user, current_user

from wikimetrics.configurables import app, db, login_manager, google, mw_oauth_token
from wikimetrics.models import UserStore
from wikimetrics.enums import UserRole
from wikimetrics.utils import json_error


def is_public(to_decorate):
    """
    Marks a Flask endpoint as public (not requiring authentication).
    """
    def decorator(f):
        f.is_public = True
        return f
    
    return decorator(to_decorate)


@app.before_request
def default_to_private():
    """
    Make authentication required by default,
    unless the endpoint requested has "is_public is True"
    """
    if current_user.is_authenticated():
        return
    
    if request.is_xhr:
        return json_error('Please Login to access {0}'.format(request.path))
    
    if (
        request.endpoint and
        not request.path.startswith('/static/') and
        not request.path == 'favicon.ico' and
        not getattr(app.view_functions[request.endpoint], 'is_public', False)
    ):
        flash('Please Login before visiting {0}'.format(request.path), 'info')
        return redirect(url_for('login', next=request.path))


@login_manager.user_loader
def load_user(user_id):
    """
    Callback required by Flask-Login.  Gets the User object from the database.
    """
    db_session = db.get_session()
    return UserStore.get(db_session, user_id)


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
    session['access_token'] = None
    db_session = db.get_session()
    if type(current_user) is UserStore:
        current_user.logout(db_session)
    logout_user()
    return redirect(url_for('home_index'))


def make_handshaker_mw():
    return Handshaker(
        app.config['META_MW_BASE_URL'] + app.config['META_MW_BASE_INDEX'],
        mw_oauth_token,
    )


@app.route('/login/meta_mw')
@is_public
def login_meta_mw():
    """
    Make a request to meta.wikimedia.org for Authentication.
    """
    session['access_token'] = None

    handshaker = make_handshaker_mw()
    redirect_url, request_token = handshaker.initiate()
    session['request_token'] = request_token
    return redirect(redirect_url)


@app.route('/auth/meta_mw')
@is_public
def auth_meta_mw():
    """
    Callback for meta.wikimedia.org to send us authentication results.
    This is responsible for fetching existing users or creating new ones.
    If a new user is created, they get the default role of GUEST and
    an email or username to match their details from the OAuth provider.
    """
    try:
        handshaker = make_handshaker_mw()
        raw_req_token = session['request_token']
        request_token = RequestToken(key=raw_req_token[0], secret=raw_req_token[1])
        access_token = handshaker.complete(request_token, request.query_string)
        session['access_token'] = access_token

        identity = handshaker.identify(access_token)
        username = identity['username']
        userid = identity['sub']

        db_session = db.get_session()
        user = None
        try:
            user = db_session.query(UserStore).filter_by(meta_mw_id=userid).one()

        except NoResultFound:
            try:
                user = UserStore(
                    username=username,
                    meta_mw_id=userid,
                    role=UserRole.GUEST,
                )
                db_session.add(user)
                db_session.commit()
            except Exception:
                db_session.rollback()
                raise

        except MultipleResultsFound:
            flash('Multiple users found with your id!!! Contact Administrator', 'error')
            return redirect(url_for('login'))

        user.login(db_session)
        if login_user(user):
            user.detach_from(db_session)
            del session['request_token']

    except Exception:
        flash('You need to grant the app permissions in order to login.', 'error')
        app.logger.exception(traceback.format_exc())
        return redirect(url_for('login'))

    redirect_to = session.get('next') or url_for('home_index')
    return redirect(urllib2.unquote(redirect_to))


@app.route('/login/google')
@is_public
def login_google():
    """
    Make a request to Google for Authentication.
    """
    session['access_token'] = None
    auth_callback = app.config['GOOGLE_REDIRECT_URI']
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
    if resp is None and request.args.get('error') == 'access_denied':
        flash('You need to grant the app permissions in order to login.', 'error')
        return redirect(url_for('login'))
    
    access_token = resp['access_token'] or request.args.get('code')
    if access_token:
        session['access_token'] = access_token, ''
        r = requests.get(app.config['GOOGLE_USERINFO_URI'], headers={
            'Authorization': 'OAuth ' + access_token
        })
        if r.ok:
            userinfo = json.loads(r.text)
            email = userinfo['email']
            id = userinfo['id']
            
            db_session = db.get_session()
            user = None
            try:
                user = db_session.query(UserStore).filter_by(google_id=id).one()
            
            except NoResultFound:
                try:
                    user = UserStore(
                        email=email,
                        google_id=id,
                        role=UserRole.GUEST,
                    )
                    db_session.add(user)
                    db_session.commit()
                except Exception:
                    db_session.rollback()
                    raise
            
            except MultipleResultsFound:
                return 'Multiple users found with your id!!! Contact Administrator'
            
            user.login(db_session)
            if login_user(user):
                user.detach_from(db_session)
                redirect_to = session.get('next') or url_for('home_index')
                redirect_to = urllib2.unquote(redirect_to)
                return redirect(redirect_to)
    
    flash('Was not allowed to authenticate you with Google.', 'error')
    return redirect(url_for('login'))


@google.tokengetter
def get_google_token():
    return session.get('access_token')


if app.config['DEBUG']:
    # safeguard against exposing this route in production
    @app.route('/login-for-testing-only')
    @is_public
    def login_for_testing_only():
        if app.config['DEBUG']:
            db_session = db.get_session()
            user = db_session.query(UserStore).filter_by(email='test@test.com').one()
            user.login(db_session)
            login_user(user)
            return ''
