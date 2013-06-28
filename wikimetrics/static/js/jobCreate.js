$(document).ready(function(){
    // set up async handlers for any async forms
    // TODO: replace with a decent plugin
    $(document).on('submit', 'form.metric-configuration', function(e){
        e.preventDefault();
        e.stopPropagation();
        
        var form = $(this);
        
        $.post(form.attr('action'), form.serialize())
            .done(function(htmlToReplaceWith){
                form.replaceWith(htmlToReplaceWith);
                // if no validation errors, save the metric into the viewModel
                if (form.find('ul.error-list').length === 0) {
                    // save to viewModel.metrics
                    // search in viewModel.metrics
                    // set metric properties
                }
            })
            .fail(function(){
            });
    });
    
    $(document).on('submit', 'form.job-request', function(e){
        // same thing as metric-configuration, but passing viewModel.request().responses()
        // as the data
    });
    
    var viewModel = {
        cohorts: ko.observableArray([]),
        toggleCohort: function(cohort){
            // fetch wikiusers
            if (!cohort.wikiusers) {
                cohort.wikiusers = ko.observableArray([]);
                $.get('/cohorts/detail/' + cohort.id, function(data){
                    cohort.wikiusers(data.wikiusers);
                }).fail(failure);
            }
            return true;
        },

        metrics: ko.observableArray([]),
        toggleMetric: function(metric){
            // TODO: this should work but... doesn't?
            // if (!metric.configure().length) {
            // metric.configure = ko.observable();
            // ...
            // metric.configure(configureForm);
            
            
            if (metric.selected()){
            // fetch form to edit metric with
                $.get('/metrics/configure/' + metric.name, function(configureForm){
                    $(metric.tabIdSelector() + '-configure').html(configureForm);
                }).fail(failure);
            } else {
                $(metric.tabIdSelector() + '-configure').html('');
            }
            return true;
        },

    };
    
    // fetch this user's cohorts
    $.get('/cohorts/list/', function(data){
        setSelected(data.cohorts);
        viewModel.cohorts(data.cohorts);
    }).fail(failure);
    
    // fetch the list of available metrics
    $.get('/metrics/list/', function(data){
        setTabIds(data.metrics, 'metric');
        setSelected(data.metrics);
        setConfigure(data.metrics);
        viewModel.metrics(data.metrics);
    }).fail(failure);
    
    // computed pieces of the viewModel
    viewModel.request = ko.observable({
        cohorts: ko.computed(function(){
            return this.cohorts().filter(function(cohort){
                return cohort.selected();
            });
        }, viewModel).extend({ throttle: 1 }),
        metrics: ko.computed(function(){
            return this.metrics().filter(function(metric){
                return metric.selected();
            });
        }, viewModel).extend({ throttle: 1 }),
    });
    
    // second level computed pieces of the viewModel
    viewModel.request().responses = ko.computed(function(){
        request = this;
        var ret = [];
        ko.utils.arrayForEach(request.metrics(), function(metric){
            ko.utils.arrayForEach(request.cohorts(), function(cohort){
                response = {
                    name: metric.label + ' - ' + cohort.name,
                    cohort: cohort,
                    metric: metric,
                    tabId: 'response-to-' + metric.id + '-for-' + cohort.id,
                };
                response.tabIdSelector = '#' + response.tabId;
                ret.push(response);
            });
        });
        
        return ret;
    }, viewModel.request());
    
    function setSelected(list){
        bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            item.selected = ko.observable(false);
        });
    };
    
    function setConfigure(list){
        bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            item.configure = ko.observable('');
        });
    };
    
    function setTabIds(list, prefix){
        if (!prefix) {
            prefix = 'should-be-unique';
        }
        bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            
            item.tabId = ko.computed(function(){
                return prefix + '-' + this.id;
            }, item);
            
            item.tabIdSelector = ko.computed(function(){
                return '#' + prefix + '-' + this.id;
            }, item);
        });
    };
    
    function failure(error){
        alert('TODO: report this error in a nicer way ' + error);
    };
    
    
    // tabs that are dynamically added won't work - fix by re-initializing
    $(".sample-result .tabbable").on("click", "a", function(e){
        e.preventDefault();
        $(this).tab('show');
    });
    
    
    // apply bindings - this connects the DOM with the view model constructed above
    ko.applyBindings(viewModel);
});
