$(document).ready(function(){
    
    var viewModel = {
        reports: ko.observableArray([]),
        refreshEvery: 5,
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
    setInterval(getReports, viewModel.refreshEvery * 1000);
    
    ko.applyBindings(viewModel);
});
