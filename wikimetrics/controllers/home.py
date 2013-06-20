from flask import render_template, redirect, request
from ..configurables import app
from ..models import *
from authentication import is_public


@app.route('/')
@is_public
def home_index():
    """
    Renders the home page.
    """
    return render_template('index.html')
