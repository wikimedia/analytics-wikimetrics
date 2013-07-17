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
                name: name,
                project: project
            }
        }).done(redirect);
    });
});
