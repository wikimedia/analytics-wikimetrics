'use strict';
/*global $:false */
var site = {
    handleWith: function(callback){
        return function(response){
            if (site.isNormalResponse(response)){
                callback.call(this, response);
            }
        };
    },

    isNormalResponse: function(response){
        if (response.isError){
            site.showError(response.message);
            return false;
        }
        if (response.isRedirect){
            site.redirect(response.redirectTo);
            return false;
        }
        site.clearMessages();
        return true;
    },

    confirmDanger: function(event, noQuestion){
        var title = $(event.target).attr('title');
        return confirm('Are you sure you want to ' + title + (noQuestion ? '' : '?') );
    },

    showError: function (message, permanent){
        site.showMessage(message, 'error', permanent);
    },
    showInfo: function (message, permanent){
        site.showMessage(message, 'info', permanent);
    },
    showWarning: function (message, permanent){
        site.showMessage(message, 'warning', permanent);
    },
    showSuccess: function (message, permanent){
        site.showMessage(message, 'success', permanent);
    },
    showMessage: function (message, category, permanent){
        site.clearMessages();

        if (!site.messageTemplate){
            site.messageTemplate = $('.messageTemplate').html();
        }
        var html = site.messageTemplate
            .replace('##message##', message)
            .replace(/##category##/g, category)
            .replace(/##permanent##/, permanent ? ' permanent' : '')
            .replace('##punctuation##', category !== 'info' ? '!' : '');
        $('.site-messages').append(html);
        $('body').scrollTop(0);
    },
    clearMessages: function (){
        $('.site-messages').children().not('.permanent').remove();
    },

    redirect: function (url){
        location.href = url;
    },

    failure: function (error){
        site.showError('Wikimetrics is experiencing problems.  Visit the Support page for help if this persists.  You can also check the console for details.');
        console.log(error);
    },

    hasValidationErrors: function(){
        return $('li.text-error').length > 0;
    },

    /**
    * Make use of this function to throttle your ajax pulls
    * when tab is not visible to the user
    * See an example on reportList.
    **/
    isVisible: function() {
        if (document.visibilityState){
            if(document.visibilityState === 'visible') {
                return true;
            } else {
                return false;
            }
        }
    },

    /*
    * Refresh rate for ajax polling
    * enter seconds, this will be converted to ms
    */
    defaultRefreshRate: 5,

    pollingActive: true,

    getRefreshRate: function() {
        var rate = site.defaultRefreshRate;
        return rate * 1000;
    },

    // ***********************************************************
    // Data population - usually done with something like Sammy JS
    // ***********************************************************
    populateCohorts: function(viewModel){
        $.get('/cohorts/list/')
            .done(site.handleWith(function(data){
                viewModel.cohorts(data.cohorts);
            }))
            .fail(site.failure);
    },

    populateMetrics: function(viewModel){
        $.get('/metrics/list/')
            .done(site.handleWith(function(data){
                viewModel.metrics(data.metrics);
            }))
            .fail(site.failure);
    },

    populateReports: function(viewModel){
        $.get('/reports/list/')
            .done(site.handleWith(function(data){
                //TODO this is a circular dependecy, reports depends on
                // list and list uses reports. this function
                // should reside on reportList

                var reportsStr = JSON.stringify(data.reports);
                var change = !viewModel.previousReportData || viewModel.previousReportData !== reportsStr;
                if (change){
                    // clone the data so we don't change viewModel.previousReportData
                    data.reports.forEach(function(report){
                        report.public = ko.observable(report.public);
                        report.success = report.status === 'SUCCESS';
                        report.failure = report.status === 'FAILURE';
                        report.publicResult = report.recurrent ?
                            '/static/public/' + report.id + '/full_report.json' :
                            '/static/public/' + report.id + '.json';
                    });
                    viewModel.reports(data.reports);
                }
                viewModel.previousReportData = reportsStr;
            }))
            .fail(site.failure);
    },

    // persists the bootstrap tab hash in the url and navigates to it on page load
    enableTabNavigation: function(){
        $('ul.nav-tabs li a').on('shown', function (e) {
            location.hash = e.target.hash;
            // negate jumping down to the tab anchor
            window.scrollTo(0, 0);
        });
        if (location.hash){
            $('ul.nav-tabs li a[href=' + location.hash + ']').click();
        } else {
            $('ul.nav-tabs li a').first().click();
        }
    },

    // ***********************************************************
    // Just some util functions so I don't have to
    // import huge libraries like Underscore
    // ***********************************************************
    keys: function(obj){
        var keys = [];
        var key;

        for(key in obj){
            if(obj.hasOwnProperty(key)){
                keys.push(key);
            }
        }

        return keys;
    },
    //Serializes object to json and verifies is an empty string
    isEmpty: function(obj){
        var empty = JSON.stringify(obj) === '{}';
        return empty;
    },

    // ***********************************************************
    // List of timezones and default timezone
    // ***********************************************************
    utcTimezone: {name: 'Coordinated Universal Time (UTC)', value: '+00:00'},

    // Add more timezones as necessary
    availableTimezones : function() {
        return [
            {name: 'UTC -12:00', value: '-12:00'},
            {name: 'UTC -11:00', value: '-11:00'},
            {name: 'UTC -10:00', value: '-10:00'},
            {name: 'UTC -09:30', value: '-09:30'},
            {name: 'UTC -09:00', value: '-09:00'},
            {name: 'UTC -08:00', value: '-08:00'},
            {name: 'UTC -07:00', value: '-07:00'},
            {name: 'UTC -06:00', value: '-06:00'},
            {name: 'UTC -05:00', value: '-05:00'},
            {name: 'UTC -04:30', value: '-04:30'},
            {name: 'UTC -04:00', value: '-04:00'},
            {name: 'UTC -03:30', value: '-03:30'},
            {name: 'UTC -03:00', value: '-03:00'},
            {name: 'UTC -02:00', value: '-02:00'},
            {name: 'UTC -01:00', value: '-01:00'},
            this.utcTimezone,
            {name: 'UTC +01:00', value: '+01:00'},
            {name: 'UTC +02:00', value: '+02:00'},
            {name: 'UTC +03:00', value: '+03:00'},
            {name: 'UTC +03:30', value: '+03:30'},
            {name: 'UTC +04:00', value: '+04:00'},
            {name: 'UTC +04:30', value: '+04:30'},
            {name: 'UTC +05:00', value: '+05:00'},
            {name: 'UTC +05:30', value: '+05:30'},
            {name: 'UTC +05:45', value: '+05:45'},
            {name: 'UTC +06:00', value: '+06:00'},
            {name: 'UTC +06:30', value: '+06:30'},
            {name: 'UTC +07:00', value: '+07:00'},
            {name: 'UTC +08:00', value: '+08:00'},
            {name: 'UTC +08:30', value: '+08:30'},
            {name: 'UTC +08:45', value: '+08:45'},
            {name: 'UTC +09:00', value: '+09:00'},
            {name: 'UTC +09:30', value: '+09:30'},
            {name: 'UTC +10:00', value: '+10:00'},
            {name: 'UTC +10:30', value: '+10:30'},
            {name: 'UTC +11:00', value: '+11:00'},
            {name: 'UTC +12:00', value: '+12:00'},
            {name: 'UTC +12:45', value: '+12:45'},
            {name: 'UTC +13:00', value: '+13:00'},
            {name: 'UTC +14:00', value: '+14:00'},
        ];
    },
};

/*
* Deealing with visibility API, looks like it is not available on jquery
* Enable/disable pooling (global setting) based on visibility
* From: https://developer.mozilla.org/en-US/docs/Web/Guide/User_experience/Using_the_Page_Visibility_API
*/
function detectVisibilityApiAndUpdatePollingSettings(obj){

    var hidden, visibilityChange;
    if (typeof document.hidden !== 'undefined') { // Opera 12.10 and Firefox 18 and later support
        hidden = 'hidden';
        visibilityChange = 'visibilitychange';
    } else if (typeof document.mozHidden !== 'undefined') {
        hidden = 'mozHidden';
        visibilityChange = 'mozvisibilitychange';
    } else if (typeof document.msHidden !== 'undefined') {
        hidden = 'msHidden';
        visibilityChange = 'msvisibilitychange';
    } else if (typeof document.webkitHidden !== 'undefined') {
        hidden = 'webkitHidden';
        visibilityChange = 'webkitvisibilitychange';
    }

    /*
    * Disable polling if UI
    * is not visible
    */
    function handleVisibilityChange() {
        if (document[hidden]) {
            obj.pollingActive = false;
        } else {
            obj.pollingActive = true;
        }
    }

    if (typeof document.addEventListener !== 'undefined' || hidden !== 'undefined') {
        document.addEventListener(visibilityChange, handleVisibilityChange, false);
    }
}

// detect visibility API and add events upon load
$(document).ready(function(){ detectVisibilityApiAndUpdatePollingSettings(site); });

// moment configuration
moment.lang('en', { calendar: {
    sameDay  : '[Today at] HH:mm z',
    lastDay  : '[Yesterday at] HH:mm z',
    nextDay  : '[Tomorrow at] HH:mm z',
    lastWeek : '[last] dddd [at] HH:mm z',
    nextWeek : 'dddd [at] HH:mm z',
    sameElse : 'YYYY-MM-DD z'
}});
