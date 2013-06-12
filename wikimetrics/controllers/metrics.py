import inspect
from flask import render_template, redirect, request
from wikimetrics.web import app
from wikimetrics import metrics


@app.route('/metrics/')
def metrics_index():
    """
    This flask endpoint returns a list of all metrics
    """
    return str(inspect.getmembers(metrics, inspect.isclass))
