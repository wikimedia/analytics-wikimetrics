from flask import render_template, redirect, request
from wikimetrics.web import app


@app.route('/')
def home_index():
    """
    This flask endpoint returns the home page
    """
    return render_template('index.html')
