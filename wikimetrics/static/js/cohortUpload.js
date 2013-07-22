$(document).ready(function(){
    
    jQuery.validator.addMethod('cohortName', function(value, element) {
        return /^[0-9_\-A-Za-z ]*$/.test(value);
    }, 'Cohort names should only contain letters, numbers, spaces, dashes, and underscores');
    
    $('form.upload-cohort').validate({
        onkeyup: false,
        // would be nice to not have to turn this off, but it conflicts with typeaheads
        onfocusout: false,
        messages: {
            name: {
                remote: 'This cohort name is taken.',
            },
            project: {
                remote: 'That project does not exist.',
            }
        },
        rules: {
            name: {
                required: true,
                cohortName: true,
                remote: '/cohorts/validate/name',
            },
            project: {
                required: true,
                remote: '/cohorts/validate/project',
            },
            csv: {
                required: true
            }
        }
    });
});
