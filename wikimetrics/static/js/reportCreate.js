// Hack to make linters complain less
// TODO: maybe use a js loader here
var ko = ko;
var site = site;

$(document).ready(function(){
    
    var viewModel = {
        filter: ko.observable(''),
        cohorts: ko.observableArray([]),
        toggleCohort: function(cohort){
            // fetch wikiusers
            if (cohort && !cohort.wikiusers) {
                cohort.wikiusers = ko.observableArray([]);
                $.get('/cohorts/detail/' + cohort.id)
                    .done(site.handleWith(function(data){
                        cohort.wikiusers(data.wikiusers);
                    }))
                    .fail(site.failure);
            }
            return true;
        },

        metrics: ko.observableArray([]),
        toggleMetric: function(metric){
            
            if (metric) {
                if (metric.selected()){
                    // fetch form to configure metric with
                    $.get('/metrics/configure/' + metric.name)
                        .done(site.handleWith(function(configureForm){
                            metric.configure(configureForm);
                            enableDateTimePicker(metric);
                        }))
                        .fail(site.failure);
                } else {
                    metric.configure('');
                }
            }
            return true;
        },
        
        save: function(formElement){
            
            if (site.hasValidationErrors()){
                site.showWarning('Please configure and click Save Configuration for each selected metric.');
                return;
            }
            
            var vm = ko.dataFor(formElement);
            if (vm.request().responses().length === 0){
                site.showWarning('Please select at least one cohort and one metric.');
                return;
            }
            
            var metricsWithoutOutput = {};
            ko.utils.arrayForEach(vm.request().responses(), function(response){
                if (!response.metric.outputConfigured()){
                    metricsWithoutOutput[response.metric.label] = true;
                }
            });
            metricsWithoutOutput = site.keys(metricsWithoutOutput);
            
            if (metricsWithoutOutput.length){
                site.showWarning(metricsWithoutOutput.join(', ') + ' do not have any output selected.');
                return;
            }
            
            var form = $(formElement);
            var data = ko.toJSON(vm.request().responses);
            data = JSON.parse(data);
            
            ko.utils.arrayForEach(data, function(response){
                delete response.metric.configure;
                delete response.cohort.wikiusers;
            });
            data = JSON.stringify(data);
            
            $.ajax({ type: 'post', url: form.attr('action'), data: {responses: data} })
                .done(site.handleWith(function(response){
                    // should redirect to the reports page, so show an error otherwise
                    site.showWarning('Unexpected: ' + JSON.stringify(response));
                }))
                .fail(site.failure);
        },
        
        saveMetricConfiguration: function(formElement){
            var metric = ko.dataFor(formElement);
            var form = $(formElement);
            var data = ko.toJS(metric);
            delete data.configure;
            
            $.ajax({ type: 'post', url: form.attr('action'), data: data })
                .done(site.handleWith(function(response){
                    metric.configure(response);
                    enableDateTimePicker(metric);
                    if (site.hasValidationErrors()){
                        site.showWarning('The configuration was not all valid.  Please check all the metrics below.');
                    } else {
                        site.showSuccess('Configuration Saved');
                    }
                }))
                .fail(site.failure);
        },
    };
    
    // fetch this user's cohorts
    $.get('/cohorts/list/')
        .done(site.handleWith(function(data){
            setSelected(data.cohorts);
            viewModel.cohorts(data.cohorts);
            // pre-select any selected cohorts
            if (location.hash){
                try {
                    viewModel.cohorts().filter(function(c){
                        return c.id === location.hash.substring(1);
                    })[0].selected(true);
                } catch(e) {}
            }
        }))
        .fail(site.failure);
    
    // fetch the list of available metrics
    $.get('/metrics/list/')
        .done(site.handleWith(function(data){
            setTabIds(data.metrics, 'metric');
            setSelected(data.metrics);
            setConfigure(data.metrics);
            setAggregationOptions(data.metrics);
            viewModel.metrics(data.metrics);
        }))
        .fail(site.failure);
    
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
        var request = this;
        var ret = [];
        ko.utils.arrayForEach(request.metrics(), function(metric){
            ko.utils.arrayForEach(request.cohorts(), function(cohort){
                var response = {
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
    
    viewModel.filteredCohorts = ko.computed(function(){
        if (this.cohorts().length && this.filter().length) {
            var filter = this.filter().toLowerCase();
            return this.cohorts().filter(function(it){
                var name = it.name.toLowerCase();
                return name.indexOf(filter) >= 0;
            });
        } else {
            return this.cohorts();
        }
    }, viewModel);
    
    function setSelected(list){
        var bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            item.selected = ko.observable(false);
        });
    }
    
    function setConfigure(list){
        var bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            item.configure = ko.observable('');
        });
    }
    
    function setAggregationOptions(list){
        var bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            item.individualResults = ko.observable(false);
            item.aggregateResults = ko.observable(true);
            item.aggregateSum = ko.observable(true);
            item.aggregateAverage = ko.observable(false);
            item.aggregateStandardDeviation = ko.observable(false);
            item.outputConfigured = ko.computed(function(){
                return this.individualResults()
                    || (
                            this.aggregateResults()
                         && (
                                this.aggregateSum()
                             || this.aggregateAverage()
                             || this.aggregateStandardDeviation()
                            )
                       );
            }, item);
        });
    }
    
    function setTabIds(list, prefix){
        if (!prefix) {
            prefix = 'should-be-unique';
        }
        var bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            
            item.tabId = ko.computed(function(){
                return prefix + '-' + this.id;
            }, item);
            
            item.tabIdSelector = ko.computed(function(){
                return '#' + prefix + '-' + this.id;
            }, item);
        });
    }
    
    function enableDateTimePicker(metric){
        var parentId = metric.tabId();
        var controls = $('#' + parentId + ' div.datetimepicker');
        controls.datetimepicker({language: 'en'});
        // TODO: this might be cleaner if it metric[name] was an observable
        controls.on('changeDate', function(){
            var input = $(this).find('input');
            var name = input.attr('name');
            metric[name] = input.val();
        });
    }
    
    // tabs that are dynamically added won't work - fix by re-initializing
    $(".sample-result .tabbable").on("click", "a", function(e){
        e.preventDefault();
        $(this).tab('show');
    });
    
    
    // apply bindings - this connects the DOM with the view model constructed above
    ko.applyBindings(viewModel);
});
