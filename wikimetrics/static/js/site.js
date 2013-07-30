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
        } else if (response.isRedirect){
            site.redirect(response.redirectTo);
            return false;
        } else {
            site.clearMessages();
            return true;
        }
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
        site.showError(error);
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
                for(j in reports){
                    reportsDict[reports[j].id] = reports[j];
                }
                for(dj in data.reports){
                    report = data.reports[dj];
                    if (report.id in reportsDict && report.status === reportsDict[report.id].status){
                        continue;
                    }
                    // if there's a difference, just replace the whole thing
                    viewModel.reports(data.reports);
                    return;
                }
            }))
            .fail(site.failure);
    },
    
    // ***********************************************************
    // Just some util functions so I don't have to
    // import huge libraries like Underscore
    // ***********************************************************
    keys: function(obj){
        var keys = [];

        for(var key in obj){
            if(obj.hasOwnProperty(key)){
                keys.push(key);
            }
        }

        return keys;
    },
};
