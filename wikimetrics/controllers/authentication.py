import json
import requests
from flask import (
    render_template,
    redirect,
    request,
    url_for,
    session,
    flash,
)
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from flask.ext.login import LoginManager, login_user, logout_user, current_user
from flask.ext.oauth import OAuth
from ..configurables import app, db, login_manager, google
from ..models import User, UserRole


def is_public(to_decorate):
    """
    Marks a Flask endpoint as public (not requiring authentication).
    """
    def decorator(f):
        f.is_public = True
        return f
    
    return decorator(to_decorate)


if app.config['DEBUG']:
    # safeguard against exposing this route in production
    @app.route('/login-for-testing-only')
    @is_public
    def login_for_testing_only():
        if app.config['DEBUG']:
            db_session = db.get_session()
            user = db_session.query(User).get(2)
            if user is None:
                user = User(
                    id=2,
                    email='test@test.com',
                )
                db_session.add(user)
                db_session.commit()
            user.login(db_session)
            login_user(user)
            return ''


@app.before_request
def default_to_private():
    """
    Make authentication required by default,
    unless the endpoint requested has "is_public is True"
    """
    if current_user.is_authenticated():
        return
    
    # TODO: put static resources in a new Blueprint
    if (
            request.endpoint
        and not 'static' in request.endpoint
        and not getattr(app.view_functions[request.endpoint], 'is_public', False)
    ):
        return redirect(url_for('login', next=request.url))


@login_manager.user_loader
def load_user(user_id):
    """
    Callback required by Flask-Login.  Gets the User object from the database.
    """
    db_session = db.get_session()
    user = User.get(db_session, user_id)
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
    db_session = db.get_session()
    if type(current_user) is User:
        current_user.logout(db_session)
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
                user = db_session.query(User).filter_by(google_id=id).one()
            
            except NoResultFound:
                user = User(
                    email=email,
                    google_id=id,
                    role=UserRole.GUEST,
                )
                db_session.add(user)
                db_session.commit()
            
            except MultipleResultsFound:
                return 'Multiple users found with your id!!! Contact Administrator'
            
            user.login(db_session)
            if login_user(user):
                user.detach_from(db_session)
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
