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
                        site.showError('Failed to save report - the report is not public', true);
                    });
            }
            else {
                $.post('/reports/unset-public/' + report.id)
                    .done(site.handleWith(function(){
                        report.public(false);
                    }))
                    .fail(function() {
                        site.showError('Failed to remove the report - the report is still public', true);
                    });
            }
            return true;
        },

        rerun: function(report, event) {
            if (site.confirmDanger(event, true)) {
                $.post('/reports/rerun/' + report.id)
                    .done(site.handleWith(function(){
                        getReports(true);
                    }))
                    .fail(function() {
                        site.showError('Failed to rerun the report', true);
                    });
            }
        },

        rerunMessage: (
            'rerun this report?\n\n' +
            'If you just have rerun this report and still got a failure, ' +
            'consider waiting some time before reruning it again; ' +
            'the problems may be external to wikimetrics. Thanks!'
        ),
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
        if (site.pollingActive) {
            site.populateReports(viewModel);
        }
        if (!once) {
            setTimeout(getReports, site.getRefreshRate());
        }
    };
    getReports();
    ko.applyBindings(viewModel);
});


