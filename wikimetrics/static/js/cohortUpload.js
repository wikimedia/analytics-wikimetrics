$(document).ready(function(){
    
    jQuery.validator.addMethod('cohortName', function(value, element) {
        return /^[0-9_\-A-Za-z ]*$/.test(value);
    }, 'Cohort names should only contain letters, numbers, spaces, dashes, and underscores');
    
    $('form.upload-cohort').validate({
        messages: {
            name: {
                remote: 'This cohort name is taken.',
            }
        },
        rules: {
            name: {
                required: true,
                cohortName: true,
                remote: '/validate/cohort/allowed'
            },
            csv: {
                required: true
            }
        }
    });
});
