from flask import Flask, redirect, request, session, url_for
from flask_login import LoginManager
from decorator import decorator

app = Flask('wikimetrics')
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)


@decorator
def is_public(f, *args, **kw):
    """
    Meant to mark a Flask endpoint as public.
    This means it does not require authentication.
    """
    f.is_public = True
    return f(*args, **kw)


import controllers


@app.before_request
def default_to_private():
    """
    Make authentication required by default,
    unless the endpoint requested has "is_public is True"
    """
    login_valid = 'user' in session
    print request.endpoint

    if (request.endpoint and
        not login_valid and
        not 'static' in request.endpoint and
        not 'login' in request.endpoint and
        not 'login_google' in request.endpoint and
        not 'login_twitter' in request.endpoint and
        not getattr(app.view_functions[request.endpoint], 'is_public', False)
    ):
        return redirect(url_for('login'))
