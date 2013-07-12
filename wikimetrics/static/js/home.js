$(document).ready(function(){
    
    var viewModel = {
        cohorts: ko.observableArray([]),
        metrics: ko.observableArray([]),
        jobs: ko.observableArray([]),
    };
    site.populateCohorts(viewModel);
    site.populateMetrics(viewModel);
    site.populateJobs(viewModel);
    
    ko.applyBindings(viewModel);
});
