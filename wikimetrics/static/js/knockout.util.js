/**
 * Custom binding that is used as follows:
 * `<section data-bind="metricConfigurationForm: property"></section>`
 * And works as follows:
 *     In the example above, property is a ko.observable or plain property that evaluates to some HTML which
 *     should be rendered inside the <section></section>
 *     The binding then sets the context for the section's child elements as the same as the current context
 */
ko.bindingHandlers.metricConfigurationForm = {
    init: function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext){
        return {
            controlsDescendantBindings: true
        };
    },
    update: function(element, valueAccessor, allBindingsAccessor, viewModel, bindingContext){
        var unwrapped, childContext;
        unwrapped = ko.utils.unwrapObservable(valueAccessor());
        if (unwrapped != null) {
            $(unwrapped).find(':input').each(function(){
                var value = '';
                var name = $(this).attr('name');
                if (!name) { return; }
                
                if ($(this).is('[type=checkbox]')){
                    value = $(this).is(':checked');
                } else {
                    value = $(this).val();
                }
                bindingContext.$data[name] = ko.observable(value);
            });
            $(element).html(unwrapped);
            childContext = bindingContext.createChildContext(bindingContext.$data);
            ko.applyBindingsToDescendants(childContext, element);
        }
    }
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
