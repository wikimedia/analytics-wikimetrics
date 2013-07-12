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
        $('.site-messages').children().remove();
        if (!site.messageTemplate){
            site.messageTemplate = $('.messageTemplate').html();
        }
        html = site.messageTemplate
            .replace('##message##', message)
            .replace(/##category##/g, category)
            .replace('##punctuation##', category !== 'info' ? '!' : '');
        $('.site-messages').append(html);
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
        $.get('/cohorts/list/', function(data){
            viewModel.cohorts(data.cohorts);
        }).fail(site.failure);
    },
    
    populateMetrics: function(viewModel){
        $.get('/metrics/list/', function(data){
            viewModel.metrics(data.metrics);
        }).fail(site.failure);
    },
    
    populateJobs: function(viewModel){
        $.get('/jobs/list/', function(data){
            viewModel.jobs(data.jobs);
        }).fail(site.failure);
    },
};
