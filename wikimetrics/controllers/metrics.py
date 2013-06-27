import inspect
from flask import render_template, redirect, request, jsonify
from ..configurables import app, db
from .. import metrics


metric_classes = {m[0]: m[1] for m in inspect.getmembers(metrics, inspect.isclass)}


@app.route('/metrics/')
def metrics_index():
    """
    Renders a page with a list of all metrics.
    """
    return jsonify(metrics=metric_classes.keys())


@app.route('/metrics/list/')
def metrics_list():
    """
    Returns a JSON response of the format:
    {'metrics' : [
            {
                'id'          : 1,
                'name'        : MetricClassName
                'label'       : 'Label',
                'description' : 'This is a long description of what the metric does'
            }
        ]
    }
    """
    records = []
    for name, metric in inspect.getmembers(metrics, inspect.isclass):
        if metric.show_in_ui:
            records.append({
                'name' : name,
                'id'   : metric.id,
                'label': metric.label,
                'description' : metric.description
            })
    return jsonify(metrics=records)


@app.route('/metrics/configure/<string:name>', methods=['GET', 'POST'])
def metrics_configure(name):
    """
    Generic endpoint that renders an html form for a specific metric
    
    Parameters:
        name    : the name of the wikimetrics.metrics.Metric subclass desired
    
    Returns:
        if validation passes or is a get, the form to edit the metric
        if validation fails, the form with the relevant errors
    """
    if request.method == 'POST':
        metric_form = metric_classes[name](request.form)
        metric_form.validate()
    elif request.method == 'GET':
        metric_form = metric_classes[name]()
    
    return render_template(
        'form.html',
        form=metric_form,
        form_class='async',
        action=request.url,
        submit_text='Save Configuration',
    )
