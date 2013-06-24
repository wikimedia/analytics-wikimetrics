$(document).ready(function(){
    var viewModel = {
        cohorts: ko.observableArray([
            {name: 'Algeria Summer Teahouse', description: '', wikiusers: ko.observableArray([])},
            {name: 'Berlin Beekeeping Society', description: '', wikiusers: ko.observableArray([])},
            {name: 'A/B April', description: '', wikiusers: ko.observableArray([])},
            {name: 'A/B March', description: '', wikiusers: ko.observableArray([])},
            {name: 'A/B February', description: '', wikiusers: ko.observableArray([])},
            {name: 'A/B January', description: '', wikiusers: ko.observableArray([])},
            {name: 'A/B December', description: '', wikiusers: ko.observableArray([])},
            {name: 'A/B October', description: '', wikiusers: ko.observableArray([])},
            {name: 'A/B September', description: '', wikiusers: ko.observableArray([])},
            {name: 'A/B August', description: '', wikiusers: ko.observableArray([])},
            {name: 'A/B July', description: '', wikiusers: ko.observableArray([])},
        ]),
        toggleCohort: function(cohort){
            console.log(cohort);
        },

        metrics: ko.observableArray([
            {name: 'Edits', id: 1, description: 'Edits made in a specified Namespace.' },
            {name: 'Bytes Added', id: 2, description: 'Bytes Added through edits.' },
            {name: 'Revert Rate', id: 3, description: 'Rate of reverted edits.' },
        ]),
        toggleMetric: function(metric){
            console.log(metric);
        },

        request: ko.observable({
            cohorts: ko.observableArray([]),
            metrics: ko.observableArray([]),
            responses: ko.observableArray([]),
        }),
    };
    
    setTabIds(viewModel.metrics, 'metric');
    setTabIds(viewModel.request().responses, 'response');
    
    ko.applyBindings(viewModel);
    
    function setTabIds(list, prefix){
        if (!prefix) {
            prefix = 'should-be-unique';
        }
        ko.utils.arrayForEach(list(), function(item){
            
            item.tabId = ko.computed(function(){
                return prefix + '-' + item.id;
            });
            
            item.tabIdSelector = ko.computed(function(){
                return '#' + prefix + '-' + item.id;
            });
        });
    }
});
