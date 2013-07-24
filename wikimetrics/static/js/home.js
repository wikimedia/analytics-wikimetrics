$(document).ready(function(){
    
    var viewModel = {
        cohorts: ko.observableArray([]),
        metrics: ko.observableArray([]),
        reports: ko.observableArray([]),
    };
    site.populateCohorts(viewModel);
    site.populateMetrics(viewModel);
    site.populateReports(viewModel);
    
    ko.applyBindings(viewModel);
});
