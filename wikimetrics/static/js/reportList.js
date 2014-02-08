$(document).ready(function(){
    var viewModel = {
        reports: ko.observableArray([]),
        
        updatePublic: function(report, event) {
            //TODO no csrf token, we need a request engine to wrap our ajax
            // requests
            if (!report.public()) {
               
                $.post('/reports/set-public/' + report.id)
                    .done(site.handleWith(function(){
                        report.public(true);
                    }))
                    .fail(function() {
                        site.showError('Failed to save report - the report is not public');
                    });
            }
            else {
                $.post('/reports/unset-public/' + report.id)
                    .done(site.handleWith(function(){
                        report.public(false);
                    }))
                    .fail(function() {
                        site.showError('Failed to remove the report - the report is still public');
                    });
            }
            return true;
        }
    };

    viewModel.reports_sorted = ko.computed(function() {
        reports = this.reports();
        if (typeof reports === 'undefined') {
            reports = [];
        }
        return this.reports().sort(function(report1, report2) {
            return moment(report2.created) - moment(report1.created);
        });
    }, viewModel);
    
    // get reports from reports/detail/endpoint
    var getReports = function (once) {
        site.populateReports(viewModel);
        if (!once) {
            setTimeout(getReports, site.getRefreshRate());
        }
    };
    getReports();
    ko.applyBindings(viewModel);
});


