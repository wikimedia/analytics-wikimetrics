// TODO: get this nasty stuff out of here
//var invalid = JSON.parse('{{ invalid_json | safe }}');
//var valid = JSON.parse('{{ valid_json | safe }}');
//var cohort_name = '{{ cohort_name }}';
//var cohort_project = '{{ cohort_project }}';
var invalid = [];
var valid = [];
var cohort_name = {};
var cohort_project = {};
$(document).ready(function(){
    ko.applyBindings({
        invalid: ko.observableArray(invalid),
        valid: ko.observableArray(valid)
    });

    $('form.finish-upload').submit(function(event){
        event.preventDefault();
        event.stopPropagation();
        
        form = $(this);
        $.ajax({
            url: form.attr('action'),
            type: 'post',
            data: {
                users: JSON.stringify(valid),
                cohort_name: cohort_name,
                cohort_project: cohort_project
            }
        }).done(redirect);
    });
});
