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
