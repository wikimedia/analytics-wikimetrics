import json
import requests
import urllib2
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
from wikimetrics.configurables import app, db, login_manager, google
from wikimetrics.models import User, UserRole
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
            request.endpoint
        and not request.path.startswith('/static/')
        and not request.path == 'favicon.ico'
        and not getattr(app.view_functions[request.endpoint], 'is_public', False)
    ):
        flash('Please Login before visiting {0}'.format(request.path), 'info')
        return redirect(url_for('login', next=request.path))


@login_manager.user_loader
def load_user(user_id):
    """
    Callback required by Flask-Login.  Gets the User object from the database.
    """
    db_session = db.get_session()
    user = User.get(db_session, user_id)
    db_session.close()
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
    db_session.close()
    logout_user()
    return redirect(url_for('home_index'))


@app.route('/login/google')
@is_public
def login_google():
    """
    Make a request to Google for Authentication.
    """
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
    if not resp and request.args.get('error') == 'access_denied':
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
                db_session.close()
                return 'Multiple users found with your id!!! Contact Administrator'
            
            user.login(db_session)
            if login_user(user):
                user.detach_from(db_session)
                db_session.close()
                redirect_to = session.get('next') or url_for('home_index')
                redirect_to = urllib2.unquote(redirect_to)
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


if app.config['DEBUG']:
    # safeguard against exposing this route in production
    @app.route('/login-for-testing-only')
    @is_public
    def login_for_testing_only():
        if app.config['DEBUG']:
            db_session = db.get_session()
            user = db_session.query(User).filter_by(email='test@test.com').one()
            user.login(db_session)
            login_user(user)
            db_session.close()
            return ''
