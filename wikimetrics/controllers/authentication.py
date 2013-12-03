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
from wikimetrics.configurables import app, db, login_manager, google, meta_mw
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
    session['access_token'] = None
    db_session = db.get_session()
    if type(current_user) is User:
        current_user.logout(db_session)
    db_session.close()
    logout_user()
    return redirect(url_for('home_index'))


@app.route('/login/meta_mw')
@is_public
def login_meta_mw():
    """
    Make a request to meta.wikimedia.org for Authentication.
    """
    session['access_token'] = None
    redirector = meta_mw.authorize()
    
    # MW's authorize requires an oauth_consumer_key
    redirector.headers['Location'] += '&oauth_consumer_key=' + meta_mw.consumer_key
    return redirector


@app.route('/auth/meta_mw')
@meta_mw.authorized_handler
@is_public
def auth_meta_mw(resp):
    """
    Callback for meta.wikimedia.org to send us authentication results.
    This is responsible for fetching existing users or creating new ones.
    If a new user is created, they get the default role of GUEST and
    an email or username to match their details from the OAuth provider.
    """
    if resp is None:
        flash('You need to grant the app permissions in order to login.', 'error')
        return redirect(url_for('login'))
    
    session['access_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )
    
    try:
        # Another hack: we need to use the Authorized: header.
        data = meta_mw.post(
            app.config['META_MW_BASE_URL'] + app.config['META_MW_USERINFO_URI'],
            content_type='text/plain'
        ).data
        username = data['query']['userinfo']['name']
        userid = data['query']['userinfo']['id']
        
        db_session = db.get_session()
        user = None
        try:
            user = db_session.query(User).filter_by(meta_mw_id=userid).one()
        
        except NoResultFound:
            user = User(
                username=username,
                meta_mw_id=userid,
                role=UserRole.GUEST,
            )
            db_session.add(user)
            db_session.commit()
        
        except MultipleResultsFound:
            db_session.close()
            return 'Multiple users found with your id!!! Contact Administrator'
        
        user.login(db_session)
        try:
            if login_user(user):
                user.detach_from(db_session)
                redirect_to = session.get('next') or url_for('home_index')
                redirect_to = urllib2.unquote(redirect_to)
                return redirect(redirect_to)
        finally:
            db_session.close()
    
    except KeyError:
        if data['error']['code'] == 'mwoauth-invalid-authorization':
            flash('Access to this application was revoked. Please re-login!')
            return redirect(url_for('login'))
    
    next_url = request.args.get('next') or url_for('index')
    return redirect(next_url)


@meta_mw.tokengetter
def get_meta_wiki_token(token=None):
    return session.get('access_token')


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
            try:
                if login_user(user):
                    user.detach_from(db_session)
                    redirect_to = session.get('next') or url_for('home_index')
                    redirect_to = urllib2.unquote(redirect_to)
                    return redirect(redirect_to)
            finally:
                db_session.close()
    
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
            user = db_session.query(User).filter_by(email='test@test.com').one()
            user.login(db_session)
            login_user(user)
            db_session.close()
            return ''
