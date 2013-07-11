$(document).ready(function(){
    
    var viewModel = {
        jobs: ko.observableArray([]),
    };
    
    viewModel.jobs_sorted = ko.computed(function() {
        jobs = this.jobs()
        if (typeof jobs === "undefined") {
            jobs = []
        }
        return this.jobs().sort(function(job1, job2) {
            return job2.created - job1.created;
        });
    }, viewModel);
    
    // get jobs from jobs/detail/endpoint
    setInterval(function () {
        $.get('/jobs/list/', function(data){
            viewModel.jobs(data.jobs);
        }).fail(failure);
    }, 2000);
    
    function failure(error){
        alert('TODO: report this error in a nicer way ' + error);
    };
    
    ko.applyBindings(viewModel);
});
