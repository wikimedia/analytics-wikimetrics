$(document).ready(function(){
    var viewModel = {
        cohorts: ko.observableArray([
            // /cohorts/list
            {id: 1, name: 'Algeria Summer Teahouse', description: '', wikiusers: [
                // /cohorts/detail/id
                {mediawiki_username: 'Dan', mediawiki_userid: 1, project: 'enwiki'},
                {mediawiki_username: 'Evan', mediawiki_userid: 2, project: 'enwiki'},
                {mediawiki_username: 'Andrew', mediawiki_userid: 3, project: 'enwiki'},
                {mediawiki_username: 'Diederik', mediawiki_userid: 4, project: 'enwiki'},
            ]},
            {id: 2, name: 'Berlin Beekeeping Society', description: '', wikiusers: [
                {mediawiki_username: 'Andrea', mediawiki_userid: 5, project: 'dewiki'},
                {mediawiki_username: 'Dennis', mediawiki_userid: 6, project: 'dewiki'},
                {mediawiki_username: 'Florian', mediawiki_userid: 7, project: 'dewiki'},
                {mediawiki_username: 'Gabriele', mediawiki_userid: 8, project: 'dewiki'},
            ]},
            {id: 3, name: 'A/B April', description: '', wikiusers: [
                {mediawiki_username: 'n/a', mediawiki_userid: 9, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 10, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 11, project: 'enwiki'},
            ]},
            {id: 4, name: 'A/B March', description: '', wikiusers: [
                {mediawiki_username: 'n/a', mediawiki_userid: 12, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 13, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 14, project: 'enwiki'},
            ]},
            {id: 5, name: 'A/B February', description: '', wikiusers: [
                {mediawiki_username: 'n/a', mediawiki_userid: 15, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 16, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 17, project: 'enwiki'},
            ]},
            {id: 6, name: 'A/B January', description: '', wikiusers: [
                {mediawiki_username: 'n/a', mediawiki_userid: 18, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 19, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 20, project: 'enwiki'},
            ]},
            {id: 7, name: 'A/B December', description: '', wikiusers: [
                {mediawiki_username: 'n/a', mediawiki_userid: 21, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 22, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 23, project: 'enwiki'},
            ]},
            {id: 8, name: 'A/B October', description: '', wikiusers: [
                {mediawiki_username: 'n/a', mediawiki_userid: 24, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 25, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 26, project: 'enwiki'},
            ]},
            {id: 9, name: 'A/B September', description: '', wikiusers: [
                {mediawiki_username: 'n/a', mediawiki_userid: 27, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 28, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 29, project: 'enwiki'},
            ]},
            {id: 10, name: 'A/B August', description: '', wikiusers: [
                {mediawiki_username: 'n/a', mediawiki_userid: 30, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 31, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 32, project: 'enwiki'},
            ]},
            {id: 11, name: 'A/B July', description: '', wikiusers: [
                {mediawiki_username: 'n/a', mediawiki_userid: 33, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 34, project: 'enwiki'},
                {mediawiki_username: 'n/a', mediawiki_userid: 35, project: 'enwiki'},
            ]},
        ]),
        toggleCohort: function(cohort){
            console.log(cohort.selected());
            return true;
        },

        // /metrics/list
        metrics: ko.observableArray([
            {name: 'NamespaceEdits', label: 'Edits', id: 1, description: 'Edits made in a specified Namespace.' },
            // form for each metric: /metrics/configure/name
            {name: 'BytesAdded', label: 'Bytes Added', id: 2, description: 'Bytes Added through edits.' },
            {name: 'RevertRate', label: 'Revert Rate', id: 3, description: 'Rate of reverted edits.' },
        ]),
        toggleMetric: function(metric){
            console.log(metric.selected());
            return true;
        },

    };
    
    setSelected(viewModel.cohorts);
    setSelected(viewModel.metrics);
    setTabIds(viewModel.metrics, 'metric');
    
    // computed pieces of the viewModel
    viewModel.request = ko.observable({
        cohorts: ko.computed(function(){
            return this.cohorts().filter(function(cohort){
                return cohort.selected();
            });
        }, viewModel),
        metrics: ko.computed(function(){
            return this.metrics().filter(function(metric){
                return metric.selected();
            });
        }, viewModel),
    });
    // second level computed pieces
    viewModel.request().responses = ko.computed(function(){
        request = this;
        var ret = [];
        ko.utils.arrayForEach(request.metrics(), function(metric){
            ko.utils.arrayForEach(request.cohorts(), function(cohort){
                response = {
                    name: metric.name + ' - ' + cohort.name,
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
    
    // apply bindings - this connects the DOM with the view model constructed above
    ko.applyBindings(viewModel);
    
    function setSelected(list){
        bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            item.selected = ko.observable(false);
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
    
    
    // tabs that are dynamically added won't work - fix by re-initializing
    $(".sample-result .tabbable").on("click", "a", function(e){
        e.preventDefault();
        $(this).tab('show');
    });
});
