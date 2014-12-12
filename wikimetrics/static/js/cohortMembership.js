/*global $:false */
/*global ko:false */
/*global document*/
/*global site*/

$(document).ready(function () {
    var validityOptions = {
        all: 'All users',
        valid: 'Valid users',
        invalid: 'Invalid users'
    };

    var delete_message = (
        'delete this user?\n\n' +
        'This user will not be included in any new reports you run on this cohort, ' +
        'but the user\'s data will not be deleted from reports you have already run.'
    );

    var delete_invalid_message = (
        'delete this user\'s invalid instances?\n\n' +
        'Its connections to non-existent or problematic projects will be removed, ' +
        'but its valid instances will continue to be included in new reports.'
    );

    var maxWikiusersShown = 20;

    var viewModel = {
        /**
         * Knockout observables
         */
        summary: ko.observable(''),
        textFilter: ko.observable(''),
        validityFilter: ko.observableArray([
            validityOptions.all,
            validityOptions.valid,
            validityOptions.invalid
        ]),
        selectedValidity: ko.observable(validityOptions.all),
        wikiusers: ko.observableArray([]),
        pageInfo: ko.observable(''),

        /**
         * Populates the knockout observables
         * given a list of wikiusers returned by the server.
         */
        populate: function (wikiusers) {
            this.wikiusers(this._formatWikiusers(wikiusers));

            var counters = this._getSummaryCounters(wikiusers);
            this.summary(
                counters.userCount + ' users in ' +
                counters.projectCount + ' projects; ' +
                counters.invalidCount + ' invalid entries'
            );
        },

        /**
         * Requests the server to delete a given user
         * and passes the invalidOnly parameter
         * if we want to delete only the user's invalid instances.
         */
        deleteWikiuser: function (wikiuser) {
            if (site.confirmDanger(event, true)){
                $.post(
                    window.location.pathname + '/delete',
                    {
                        username: wikiuser.username,
                        invalidOnly: event.target.getAttribute('data-delete-invalid')
                    }
                ).done(site.handleWith(function (data) {
                    if (data.isError){
                        site.showError(data.message);
                    } else {
                        fetchContents();
                    }
                })).fail(site.failure);
            }
        },

        /**
         * Messages for the confirmation dialogs
         */
        delete_message: delete_message,
        delete_invalid_message: delete_invalid_message,

        /**
         * Transforms the wikiusers received from the server
         * into a format that Knockout can interpret
         * and render the records of the table.
         */
        _formatWikiusers: function (wikiusers) {
            return ko.utils.arrayMap(wikiusers, function (wikiuser) {
                var formatted = {
                    // Username column
                    username: wikiuser.username
                };

                // Project column
                var projectCount = wikiuser.projects.length;
                if (projectCount === 1) {
                    formatted.project = wikiuser.projects[0];
                    formatted.projectTitle = '';
                } else {
                    formatted.project = projectCount + ' projects';
                    formatted.projectTitle = wikiuser.projects.join(', ');
                }

                // Valid column
                var invalidCount = wikiuser.invalidProjects.length;
                formatted.validTitle = '';
                formatted.showDeleteInvalid = false;
                if (invalidCount === 0) {
                    formatted.valid = 'Yes';
                } else if (invalidCount < projectCount) {
                    formatted.valid = 'Partially (' + invalidCount + ' invalid projects)';
                    formatted.validTitle = wikiuser.invalidProjects.join(', ');
                    formatted.showDeleteInvalid = true;
                } else if (wikiuser.invalidReasons[0] !== '') {
                    formatted.valid = 'No (' + wikiuser.invalidReasons[0] + ')';
                } else {
                    formatted.valid = 'Validation pending';
                }

                return formatted;
            });
        },

        /**
         * Returns the stats that will appear
         * in the cohorts summary (in the title).
         */
        _getSummaryCounters: function (wikiusers) {
            var distinctProjects = {},
                invalidCount = 0;

            ko.utils.arrayForEach(wikiusers, function (wikiuser) {
                ko.utils.arrayForEach(wikiuser.projects, function (project) {
                    distinctProjects[project] = true;
                });
                if (wikiuser.invalidProjects.length > 0) {
                    invalidCount += 1;
                }
            });

            return {
                userCount: wikiusers.length,
                projectCount: Object.keys(distinctProjects).length,
                invalidCount: invalidCount
            };
        },

        /**
         * Returns the string that gives information
         * about the wikiusers actually shown in the page.
         */
        _getPageInfo: function (wikiusersShown, totalWikiusers) {
            return (
                'Showing ' + wikiusersShown +
                ' of ' + totalWikiusers + ' entries.' +
                (
                    wikiusersShown < totalWikiusers ?
                    ' Please, use the filters to narrow your search.' :
                    ''
                )
            );
        }
    };

    /**
     * Gets called when any filter is updated,
     * and returns the wikiusers to be shown in the page.
     * It filters using the text filter and the validity drop-down.
     * For usability reasons, we can not show always all
     * the wikiusers. Instead, we show the first <maxWikiusersShown>.
     */
    viewModel.filteredWikiusers = ko.computed(function () {
        var textFilter = this.textFilter().toLowerCase(),
            selectedValidity = this.selectedValidity();

        var filtered = this.wikiusers().filter(function (wikiuser) {
            var username = wikiuser.username.toLowerCase(),
                validity = (
                    wikiuser.valid === 'Yes' ?
                    validityOptions.valid :
                    validityOptions.invalid
                );

            return (
                username.indexOf(textFilter) >= 0 &&
                (
                    selectedValidity === validityOptions.all ||
                    validity === selectedValidity
                )
            );
        });

        var toShow = filtered.slice(0, maxWikiusersShown);
        this.pageInfo(this._getPageInfo(toShow.length, filtered.length));

        return toShow;
    }, viewModel);

    /**
     * Gets the wikiusers from the server
     * and calls the populate method when finished.
     */
    var fetchContents = function () {
        $.get(window.location.pathname + '?full_detail=true')
            .done(site.handleWith(function (data) {
                viewModel.populate(data.membership);
            }))
            .fail(site.failure);
    };

    fetchContents();

    ko.applyBindings(viewModel);
});
