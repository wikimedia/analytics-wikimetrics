import inspect
from flask import render_template, redirect, request
from ..configurables import app
from .. import metrics


@app.route('/metrics/')
def metrics_index():
    """
    Renders a page with a list of all metrics.
    """
    return str(inspect.getmembers(metrics, inspect.isclass))
