import inspect
from flask import render_template, redirect, request, jsonify
from ..configurables import app
from .. import metrics


metric_classes = {m[0]: m[1] for m in inspect.getmembers(metrics, inspect.isclass)}


@app.route('/metrics/')
def metrics_index():
    """
    Renders a page with a list of all metrics.
    """
    return jsonify(metric_classes.keys())


@app.route('/metrics/configure/<string:name>')
def metrics_configure(name):
    """
    Generic endpoint that renders an html form for a specific metric
    
    Parameters:
        name    : the name of the wikimetrics.metrics.Metric subclass desired
    
    Returns:
        an html form that can be used to configure the specified metric
    """
    metric_form = metric_classes[name]()
    return render_template('form.html', form=metric_form)
