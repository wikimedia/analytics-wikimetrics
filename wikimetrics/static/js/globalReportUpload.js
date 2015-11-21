$(document).ready(function(){

    ko.applyBindings({
        // Timezone list and defaults
        availableTimezones : ko.observableArray(site.availableTimezones()),
        timezone: ko.observable(site.utcTimezone),
    });
});
