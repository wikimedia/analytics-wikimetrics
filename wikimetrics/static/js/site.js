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
    
    confirmDanger: function(event){
        var title = $(event.target).attr('title');
        return confirm('Are you sure you want to ' + title + '?');
    },
    
    showError: function (message){
        site.showMessage(message, 'error');
    },
    showInfo: function (message){
        site.showMessage(message, 'info');
    },
    showWarning: function (message){
        site.showMessage(message, 'warning');
    },
    showSuccess: function (message){
        site.showMessage(message, 'success');
    },
    showMessage: function (message, category){
        site.clearMessages();
        
        if (!site.messageTemplate){
            site.messageTemplate = $('.messageTemplate').html();
        }
        html = site.messageTemplate
            .replace('##message##', message)
            .replace(/##category##/g, category)
            .replace('##punctuation##', category !== 'info' ? '!' : '');
        $('.site-messages').append(html);
        $('body').scrollTop(0);
    },
    clearMessages: function (){
        $('.site-messages').children().remove();
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
                reports = viewModel.reports();
                reportsDict = {};
                reports.forEach(function(report){
                    reportsDict[report.id] = report;
                });
                data.reports.forEach(function(report){
                    report.public = ko.observable(report.public);
                });
                data.reports.forEach(function(report){
                    if (reportsDict[report.id] !== undefined && report.status === reportsDict[report.id].status){
                        return true;
                    }
                    // if there's a difference, just replace the whole thing
                    viewModel.reports(data.reports);
                    return false;
                });
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
