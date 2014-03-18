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
            .replace(/##permanent##/, !!permanent ? ' permanent':'')
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
    
    refreshEvery: 5,
    getRefreshRate: function() {
        /* if not visible refresh rate is lower */
        var rate = site.refreshEvery; /* enter seconds, this will be converted to ms*/
        if (!site.isVisible()){
            rate = rate * 10;
        }
        return rate*1000;
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
                var change = !viewModel.previousReportData || viewModel.previousReportData != reportsStr;
                if (change){
                    // clone the data so we don't change viewModel.previousReportData
                    data.reports.forEach(function(report){
                        report.public = ko.observable(report.public);
                        report.success = report.status === 'SUCCESS';
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
            $('ul.nav-tabs li a[href='+location.hash+']').click();
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
    }
};
