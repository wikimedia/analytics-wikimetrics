import json
import csv
from flask import url_for, flash, render_template, redirect, request
from ..configurables import app, db
from authentication import is_public


@app.route('/support/')
@is_public
def support_index():
    """
    Renders a page with the details on how to get support for the Wikimetrics project.
    """
    return render_template('support.html')
