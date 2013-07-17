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
        $('body').scrollTop(0);
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
            jobs = viewModel.jobs();
            jobsDict = {};
            for(j in jobs){
                jobsDict[jobs[j].id] = jobs[j];
            }
            for(dj in data.jobs){
                job = data.jobs[dj];
                if (job.id in jobsDict && job.status === jobsDict[job.id].status){
                    continue;
                }
                // if there's a difference, just replace the whole thing
                viewModel.jobs(data.jobs);
                return;
            }
        }).fail(site.failure);
    },
};
