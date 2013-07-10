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
        if (!site.errorTemplate){
            site.errorTemplate = $('.errorTemplate').html();
        }
        $('.site-messages').append(site.errorTemplate.replace('#####', message));
    },
    showInfo: function (message){
        if (!site.infoTemplate){
            site.infoTemplate = $('.infoTemplate').html();
        }
        $('.site-messages').append(site.infoTemplate.replace('#####', message));
    },
    
    redirect: function (url){
        location.href = url;
    },
    
    failure: function (error){
        site.showError(error);
    },
};
