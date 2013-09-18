$(document).ready(function(){
    
    var viewModel = {
        reports: ko.observableArray([]),
    };
    
    viewModel.reports_sorted = ko.computed(function() {
        reports = this.reports()
        if (typeof reports === "undefined") {
            reports = []
        }
        return this.reports().sort(function(report1, report2) {
            return moment(report2.created) - moment(report1.created);
        });
    }, viewModel);
    
    // get reports from reports/detail/endpoint
    getReports = function () {
        site.populateReports(viewModel);
    };
    getReports();
    setInterval(getReports, 10000);
    
    ko.applyBindings(viewModel);
});
