$(document).ready(function(){
    ko.applyBindings({
        invalid: ko.observableArray(from_the_server.invalid),
        valid: ko.observableArray(from_the_server.valid)
    });

    $('form.finish-upload').submit(function(event){
        event.preventDefault();
        event.stopPropagation();
        
        form = $(this);
        $.ajax({
            url: form.attr('action'),
            type: 'post',
            data: {
                users: JSON.stringify(from_the_server.valid),
                name: from_the_server.name,
                project: from_the_server.project
            }
        }).done(site.handleWith(function(response){
            // should redirect to the cohorts page, so show an error otherwise
            site.showWarning('Unexpected: ' + JSON.stringify(response));
        }))
        .fail(site.failure);
    });
});
