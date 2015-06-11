'use strict';
/**
 * Custom binding that is used as follows:
 *
 * `<section data-bind="metricConfigurationForm: {
 *      content: property,
 *      defaults: defaults
 * }"></section>`
 *
 * Parameters
 *      content  : is a ko.observable or plain property that evaluates to some HTML
 *                 which should be rendered inside the <section></section>
 *
 *      defaults : a set of observables that may control the value of the
 *                 input elements inside the configuration HTML
 *
 * This binding passes the current context to the child elements
 */
ko.bindingHandlers.metricConfigurationForm = {
    init: function(){
        return {
            controlsDescendantBindings: true
        };
    },
    update: function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext){
        var unwrapped = ko.unwrap(valueAccessor()),
            content = ko.unwrap(unwrapped.content),
            // must be careful when accessing defaults below, we don't want to re-create the form
            defaults = unwrapped.defaults,
            childContext = bindingContext.createChildContext(bindingContext.$data);

        if (content) {
            bindingContext.subscriptions = [];

            $(content).find(':input,div.datetimepicker').each(function(){
                var value = '';
                var name = $(this).attr('name');
                if (!name) { return; }

                if (defaults[name] && defaults[name].peek() != null) {
                    value = (
                        defaults[name].localDate ?
                            defaults[name].localDate :
                            defaults[name]
                    ).peek();
                } else if ($(this).is('[type=checkbox]')){
                    value = $(this).is(':checked');
                // support date time picker containers that don't have an input
                } else if ($(this).is('.datetimepicker')) {
                    value = $(this).data('value');
                } else {
                    value = $(this).val();
                }
                var inputObservable = ko.observable(value);
                bindingContext.$data[name] = inputObservable;

                // set up subscriptions to the defaults
                // This is important to do as subscriptions, otherwise the binding will
                //   think there's a dependency on defaults and run update each time a default is set,
                if (defaults[name]) {
                    bindingContext.subscriptions.push(
                        defaults[name].subscribe(function(val){
                            inputObservable(val);
                        })
                    );
                }
            });

            $(element).html(content);
            ko.applyBindingsToDescendants(childContext, element);

        } else {
            $(element).html('');

            if (bindingContext.subscriptions) {
                // if this update is un-selecting this metric, dispose its subscriptions
                // This is important, otherwise de-selected metrics will retain their subscriptions and
                //   continue to receive updates
                ko.bindingHandlers.metricConfigurationForm.unsubscribe(bindingContext);
            }
        }

        // also clean up subscriptions on parent disposal
        ko.utils.domNodeDisposal.addDisposeCallback(element, function () {
            ko.bindingHandlers.metricConfigurationForm.unsubscribe(bindingContext);
        });
    },
    unsubscribe: function (bindingContext) {
        bindingContext.subscriptions.forEach(function (s) { s.dispose(); });
    },
};

/**
 * Custom binding that adds bootstrap typeahead functionality to any input:
 * `<input data-bind="autocomplete: property()"></section>`
 * And works as follows:
 *     In the example above, property is a ko.observableArray holding an autocomplete list
 */
ko.bindingHandlers.autocomplete = {
    init: function(element){
        $(element).attr('autocomplete', 'off');
        $(element).data('provide', 'typeahead');
    },
    update: function(element, valueAccessor) {
        var unwrapped = ko.unwrap(valueAccessor);

        if (unwrapped !== null) {
            // typeaheads are made to be unmutable in bootstrap
            // so we 'kind of' destroy it and create it again
            $(element).data('typeahead', null);
            $(element).unbind('keyup');
            $(element).typeahead({'source': unwrapped, 'minLength': 2});
        }
    }
};

/**
 * Custom binding used as follows:
 * `<div data-bind="datetimepicker: {change: newValueFunction, timezone: timezone}">
 *    <input type="text" name="..." data-bind="value: observableValue"/>
 *  </div>`
 * And works as follows:
 *      The change parameter gets a function that receives the new date value when it changes
 *        and does whatever it needs with it.
 *      The timezone parameter is optional and converts the value to the specified timezone
 *
 * NOTE: you must wrap this around an existing input field, because the common use case
 *       is to use WTForms to generate the form field with defaults, etc. controlled and
 *       tested in the python code.
 */
ko.bindingHandlers.datetimepicker = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext){
        var val = valueAccessor(),
            timezone = val.timezone,
            zonedDate = val.value,
            defaultDate = ko.unwrap(zonedDate) || val.defaultDate,
            inputId = val.inputId,
            // set up an observable to track the date selected
            localDate = ko.observable(ko.unwrap(zonedDate)).withPausing(),

            dateFormat = ko.bindingHandlers.datetimepicker.dateFormat,
            dataFormat = ko.bindingHandlers.datetimepicker.dataFormat,

            // add any boilerplate html needed to make datepicker work
            container = $('<div class="input-append date"/>');

        // since usually we'll want to update the local date, but usually
        // we'll only have external access to the zoned date, we need a ref
        zonedDate.localDate = localDate;

        $(element).append(container);

        container.append(
            $('<input type="text">')
                .attr('id', inputId)
                .attr('data-format', dataFormat)
        );

        container.append(
            $('<span class="add-on">' +
                '<i data-time-icon="icon-time" data-date-icon="icon-calendar"></i>' +
            '</span>')
        );

        container.datetimepicker({language: 'en'});

        // the datepicker automatically sets the value of all the input elements inside
        // the container to the local formatted date.  To keep our hidden form element
        // free of this glitch, we append it after the container
        container.after(
            $('<input type="hidden">')
                .attr('name', inputId)
                .attr('data-bind', 'value: zonedDate')
        );

        // update the local date on date changes, so it can update the computed
        container.on('changeDate', function (dataWrapper) {
            localDate(dataWrapper.date);
        });

        if (defaultDate) {
            container.data('datetimepicker').setDate(moment.utc(defaultDate).toDate());
        }

        // write to the zoned date observable whenever the local date or timezone change
        ko.computed(function () {
            var local = ko.unwrap(localDate),
                zone = ko.unwrap(timezone);

            if (!local) {
                zonedDate(null);
                return;
            }

            if (!zone || !zone.value) {
                return;
            }

            zonedDate(
                moment.utc(
                    // strip out the local time zone by pretending the value is in UTC
                    moment.utc(local).format(dateFormat) + ' '
                    // then add the timezone back and parse the whole thing as a new date
                    + zone.value
                ).format(dateFormat)
            );
        });

        // if an outsider changes the zoned date, set the date of the picker directly
        var subscription = zonedDate.subscribe(function (zoned) {
            var zone = ko.unwrap(timezone);

            if (!zone || !zone.value) {
                return;
            }

            // do the opposite of above, get the local date from the zoned
            var local = moment(zoned).add(
                parseInt(zone.value), 'hours'
            ).format(dateFormat);

            // because the dom disposal below doesn't work, just ignore these errors
            try {
                // this may fire multiple times for ghost containers!! :(
                container.data('datetimepicker').setDate(local);
                localDate.sneakyUpdate(local);
            } catch (e) { return; }
        });

        // set up the binding context on the child hidden input to make sure the zoned
        // date is also available as a form element if used in a normal form
        var childContext = bindingContext.createChildContext(bindingContext.$data);
        childContext.zonedDate = zonedDate;
        ko.applyBindingsToDescendants(childContext, element);

        // TODO: for whatever reason, this doesn't fire when the metric is de-selected
        ko.utils.domNodeDisposal.addDisposeCallback(element, function () {
            subscription.dispose();
        });

        return { controlsDescendantBindings: true };
    }
};
ko.bindingHandlers.datetimepicker.dataFormat = 'yyyy-MM-dd hh:mm:ss';
ko.bindingHandlers.datetimepicker.dateFormat = 'YYYY-MM-DD HH:mm:ss';


// hacky type of observable that can be paused so it doesn't notify subscribers
// thanks to RP Niemeier: http://stackoverflow.com/a/17984353/180664
ko.observable.fn.withPausing = function() {
    this.notifySubscribers = function() {
        if (!this.pauseNotifications) {
            ko.subscribable.fn.notifySubscribers.apply(this, arguments);
        }
    };

    this.sneakyUpdate = function(newValue) {
        this.pauseNotifications = true;
        this(newValue);
        this.pauseNotifications = false;
    };

    return this;
};
