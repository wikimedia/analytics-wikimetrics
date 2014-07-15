import json
import requests
import urllib2
import jwt
import time
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
    try:
        user = UserStore.get(db_session, user_id)
    finally:
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
    try:
        if type(current_user) is UserStore:
            current_user.logout(db_session)
    finally:
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


def process_mw_jwt(identify_token_encoded):
    try:
        identify_token = jwt.decode(
            identify_token_encoded,
            app.config['META_MW_CLIENT_SECRET']
        )
        
        # Verify the issuer is who we expect (server sends $wgCanonicalServer)
        iss = urllib2.urlparse.urlparse(identify_token['iss']).netloc
        mw_domain = urllib2.urlparse.urlparse(app.config['META_MW_BASE_URL']).netloc
        if iss != mw_domain:
            raise Exception('JSON Web Token Validation Problem, iss')
        
        # Verify we are the intended audience
        if identify_token['aud'] != app.config['META_MW_CONSUMER_KEY']:
            raise Exception('JSON Web Token Validation Problem, aud')
        
        # Verify we are within the time limits of the token.
        # Issued at (iat) should be in the past
        now = int(time.time())
        if int(identify_token['iat']) > now:
            raise Exception('JSON Web Token Validation Problem, iat')
        
        # Expiration (exp) should be in the future
        if int(identify_token['exp']) < now:
            raise Exception('JSON Web Token Validation Problem, exp')
        
        # Verify we haven't seen this nonce before,
        # which would indicate a replay attack
        # TODO: implement nonce but this is not high priority
        #if identify_token['nonce'] != <<original request nonce>>
            #raise Exception('JSON Web Token Validation Problem, nonce')
        
        return identify_token
    except Exception, e:
        flash(e.message)
        raise e


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
        identify_token_encoded = meta_mw.post(
            app.config['META_MW_BASE_URL'] + app.config['META_MW_IDENTIFY_URI'],
        ).data
        identify_token = process_mw_jwt(identify_token_encoded)
        
        username = identify_token['username']
        userid = identify_token['sub']
        
        db_session = db.get_session()
        user = None
        try:
            user = db_session.query(UserStore).filter_by(meta_mw_id=userid).one()
        
        except NoResultFound:
            user = UserStore(
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
    
    except Exception, e:
        flash('Access to this application was revoked. Please re-login!')
        app.logger.exception(str(e))
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
                user = db_session.query(UserStore).filter_by(google_id=id).one()
            
            except NoResultFound:
                user = UserStore(
                    email=email,
                    google_id=id,
                    role=UserRole.GUEST,
                )
                db_session.add(user)
                db_session.commit()
            
            except MultipleResultsFound:
                db_session.close()
                return 'Multiple users found with your id!!! Contact Administrator'
            
            try:
                user.login(db_session)
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
            try:
                user = db_session.query(UserStore).filter_by(email='test@test.com').one()
                user.login(db_session)
                login_user(user)
            finally:
                db_session.close()
            return ''
