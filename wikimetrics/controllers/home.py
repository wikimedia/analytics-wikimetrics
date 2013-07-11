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


@app.route('/favicon.ico')
@is_public
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')
