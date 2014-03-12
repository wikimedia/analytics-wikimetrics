from flask import render_template, send_from_directory, url_for
from wikimetrics.configurables import app
from authentication import is_public


@app.route('/')
@is_public
def home_index():
    """
    Renders the home page.
    """
    return render_template('index.html')


@app.route('/about')
@is_public
def home_about():
    """
    Renders the about page
    """
    return render_template('about.html')


@app.route('/support')
@is_public
def support_index():
    """
    Renders a page with the details on how to get support for the Wikimetrics project.
    """
    return render_template('support.html')


@app.route('/contact')
@is_public
def contact_index():
    """
    Renders the contact page
    """
    return render_template('contact.html')


@app.route('/favicon.ico')
@is_public
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    """
    Cache-busting version of url_for, works only for static files
    """
    if endpoint and endpoint.strip() == 'static':
        values['v'] = app.config['WIKIMETRICS_LATEST']
    return url_for(endpoint, **values)
