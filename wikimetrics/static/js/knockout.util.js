/**
 * Custom binding that is used as follows:
 * `<section data-bind="subview: observableProperty"></section>`
 * And works as follows:
 *     In the example above, observableProperty is a ko.observable whose value is an object that has a `template` property
 *     The binding finds the template with id `observableProperty().template` and fills it as the innerHTML of the section element
 *     The binding then sets the context for the section's child elements as the observableProperty (like with: observableProperty)
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
