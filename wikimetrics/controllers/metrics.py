import inspect
from flask import render_template, request, jsonify
from ..configurables import app
from .. import metrics
from ..metrics import metric_classes


def get_metrics(add_class=False):
    records = []
    for name, metric in metric_classes.iteritems():
        if metric.show_in_ui:
            new_record = {
                'name' : name,
                'id'   : metric.id,
                'label': metric.label,
                'description' : metric.description,
            }
            if add_class:
                new_record['metricClass'] = metric
            
            records.append(new_record)
    return sorted(records, key=lambda r: r['label'])


@app.route('/metrics/')
def metrics_index():
    """
    Renders a page which will fetch a list of all metrics.
    """
    return render_template('metrics.html', metrics=get_metrics(add_class=True))


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
    records = get_metrics()
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
        'forms/metric_configuration.html',
        form=metric_form,
        action=request.path,
    )
