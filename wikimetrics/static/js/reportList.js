$(document).ready(function(){
    var viewModel = {
        reports: ko.observableArray([]),
        refreshEvery: 5,
        public_clicked: function(report, event) {
            var report_id = report.id;
            var checkbox = event.target;
            if (checkbox.checked) {
                $.post('/reports/save/' + report_id).fail(function() {
                    site.showError("Failed to save report - the report is not public");
                    report.public(false);
                });
            }
            else {
                $.post('/reports/remove/' + report_id).fail(function() {
                    site.showError("Failed to remove the report - the report is still public");
                    report.public(false);
                });
            }
            return true;
        }
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

