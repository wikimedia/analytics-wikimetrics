$(document).ready(function(){
    
    var viewModel = {
        cohorts: ko.observableArray([]),
        metrics: ko.observableArray([]),
        reports: ko.observableArray([]),
    };
    
    $.get('/reports/')
        .done(function(response){
            // fail silently since this is the home page
            if(!response.isError){
                site.populateCohorts(viewModel);
                site.populateMetrics(viewModel);
                site.populateReports(viewModel);
            }
        })
    
    ko.applyBindings(viewModel);
});
