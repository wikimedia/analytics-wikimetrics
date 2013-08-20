from flask import render_template, send_from_directory
from ..configurables import app
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


@app.route('/favicon.ico')
@is_public
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')
