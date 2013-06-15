from flask import Flask, redirect, request, session, url_for
from flask.ext.login import LoginManager, current_user

app = Flask('wikimetrics')
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)


def is_public(to_decorate):
    """
    Marks a Flask endpoint as public (not requiring authentication).
    """
    def decorator(f):
        f.is_public = True
        return f
    return decorator(to_decorate)


import controllers


@app.before_request
def default_to_private():
    """
    Make authentication required by default,
    unless the endpoint requested has "is_public is True"
    """
    if current_user.is_authenticated():
        return

    if (request.endpoint and
        not 'static' in request.endpoint and
        not getattr(app.view_functions[request.endpoint], 'is_public', False)
    ):
        return redirect(url_for('login'))
