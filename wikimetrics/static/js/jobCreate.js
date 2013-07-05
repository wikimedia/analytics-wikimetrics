$(document).ready(function(){
    
    var viewModel = {
        cohorts: ko.observableArray([]),
        toggleCohort: function(cohort){
            // fetch wikiusers
            if (cohort && !cohort.wikiusers) {
                cohort.wikiusers = ko.observableArray([]);
                $.get('/cohorts/detail/' + cohort.id, function(data){
                    cohort.wikiusers(data.wikiusers);
                }).fail(failure);
            }
            return true;
        },

        metrics: ko.observableArray([]),
        toggleMetric: function(metric){
            
            if (metric) {
                if (metric.selected()){
                    // fetch form to configure metric with
                    $.get('/metrics/configure/' + metric.name, function(configureForm){
                        metric.configure(configureForm);
                    }).fail(failure);
                } else {
                    metric.configure('');
                }
            }
            return true;
        },
        
        save: function(formElement){
            var vm = ko.dataFor(formElement);
            var form = $(formElement);
            var data = ko.toJSON(vm.request().responses);
            data = JSON.parse(data);
            ko.utils.arrayForEach(data, function(response){
                delete response.metric.configure;
                delete response.cohort.wikiusers;
            });
            data = JSON.stringify(data);
            
            $.ajax({
                type: 'post',
                url: form.attr('action'),
                data: {responses: data},
            }).done(function(response){
                alert(response);
            }).fail(failure);
        },
        
        saveMetricConfiguration: function(formElement){
            var metric = ko.dataFor(formElement);
            var form = $(formElement);
            var data = ko.toJS(metric);
            delete data.configure;
            
            $.ajax({
                type: 'post',
                url: form.attr('action'),
                data: data,
            }).done(function(htmlToReplaceWith){
                metric.configure(htmlToReplaceWith);
            }).fail(failure);
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