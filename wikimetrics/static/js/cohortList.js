/*global $:false */
/*global ko:false */
/*global document*/
/*global site*/
/*global setTimeout*/
$(document).ready(function(){
    var initialTagList = [];
    try {
        initialTagList = JSON.parse($('#tagsForAutocomplete').text());
    } catch (e){}

    var viewModel = {
        filter: ko.observable(''),
        cohorts: ko.observableArray([]),
        tagsAutocompleteList: ko.observableArray(initialTagList),

        populate: function(cohort, data){
            cohort.validated(data.validated);
            cohort.wikiusers(data.wikiusers);
            viewModel._populateTags(cohort, data);

            var v = data.validation;
            cohort.delete_message(v.delete_message);
            cohort.has_validation_info(!site.isEmpty(v));
            cohort.validated_count(v.validated_count);
            cohort.valid_count(v.valid_count);
            cohort.invalid_count(v.invalid_count);
            cohort.total_count(v.total_count);
            cohort.validation_status(v.validation_status);
        },

        _populateTags: function(cohort, data){
            cohort.tags(data.tags.map(function(t){
                t.highlight = ko.observable(false);
                return t;
            }));
        },

        _populateAutocomplete: function(data){
            this.tagsAutocompleteList(JSON.parse(data.tagsAutocompleteList));
        },

        view: function(cohort, event, callback){
            $.get('/cohorts/detail/' + cohort.id)
                .done(site.handleWith(function(data){
                    viewModel.populate(cohort, data);
                    if (callback){
                        callback.call();
                    }
                }))
                .fail(site.failure);
        },

        loadWikiusers: function(cohort, event){
            $.get('/cohorts/detail/' + cohort.id + '?full_detail=true')
                .done(site.handleWith(function(data){
                    viewModel.populate(cohort, data);
                    $(event.target).remove();
                }))
                .fail(site.failure);
        },

        deleteCohort: function(cohort, event){
            if (site.confirmDanger(event, true)){
                $.post('/cohorts/delete/' + cohort.id)
                    .done(site.handleWith(function(){
                        site.showWarning('Something is wrong, you should be redirected');
                    }))
                    .fail(site.failure);
            }
        },

        validateWikiusers: function(cohort, event){
            if (site.confirmDanger(event)){
                $.post('/cohorts/validate/' + cohort.id)
                    .done(site.handleWith(function(data){
                        viewModel.view(cohort, event, function(){
                            site.showInfo(data.message);
                        });
                    }))
                    .fail(site.failure);
            }
        },

        addTag: function(){
            /*
             * turns tag lowercase and replaces ' ' with '-'
             */
            function parseTag(tag){
                return tag.replace(/\s+/g, "-").toLowerCase();
            }
            var cohort = this;
            var tag = parseTag(cohort.tag_name_to_add());
            //Make sure match is exact
            var existing = null;
            $.each(cohort.tags(), function(){
                if (this.name === tag){
                    existing = this;
                    return false;
                }
            });
            if (!existing){
                $.post('/cohorts/' + cohort.id + '/tag/add/' + tag)
                    .done(site.handleWith(function(data){
                        if(data.exists){
                            site.showWarning('A similar tag already exists on this cohort');
                        }
                        else{
                            viewModel._populateTags(cohort, data);
                            viewModel._populateAutocomplete(data);
                        }
                    }))
                    .fail(site.failure);
            } else {
                existing.highlight(true);
                setTimeout(function(){
                    existing.highlight(false);
                }, 1500);
            }
            cohort.tag_name_to_add('');
        },

        deleteTag: function(tag){
            var cohort = this;
            $.post('/cohorts/' +  cohort.id + '/tag/delete/' + tag.id)
                .done(site.handleWith(function(){
                    cohort.tags.remove(tag);
                    // NOTE: autocomplete doesn't change
                    // because tags are only removed from the cohort
                }))
                .fail(site.failure);
        }
    };

    viewModel.filteredCohorts = ko.computed(function(){
        if (this.cohorts().length && this.filter().length) {
            var filter = this.filter().toLowerCase();
            return this.cohorts().filter(function(it){
                var name = it.name.toLowerCase();
                return name.indexOf(filter) >= 0;
            });
        }
        return this.cohorts();
    }, viewModel);

    // fetch this user's cohorts
    $.get('/cohorts/list/?include_invalid=true')
        .done(site.handleWith(function(data){
            setBlankProperties(data.cohorts);
            viewModel.cohorts(data.cohorts);
            site.enableTabNavigation();
        }))
        .fail(site.failure);

    ko.applyBindings(viewModel);

    function setBlankProperties(list){

        var bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            // TODO: auto-map the new properties
            item.wikiusers = ko.observableArray([]);
            item.has_validation_info = ko.observable(true);
            item.validated = ko.observable(false);
            item.validated_count = ko.observable(0);
            item.invalid_count = ko.observable(0);
            item.valid_count = ko.observable(0);
            item.total_count = ko.observable(0);
            item.validation_status = ko.observable();
            item.delete_message = ko.observable();
            item.tag_name_to_add = ko.observable();
            item.tags = ko.observableArray([]);

            item.can_run_report = ko.computed(function(){
                return !this.has_validation_info() ||
                       (this.validated() && this.valid_count() > 0);
            }, item);
            item.validating = ko.computed(function(){
                return this.validation_status() !== 'SUCCESS';
            }, item);
            item.validation_progress = ko.computed(function(){
                return this.validated_count() === this.total_count() &&
                       this.validated_count() > 0 &&
                       !this.validated() ?
                    'FINISHING_UP' : this.validation_status();
            }, item);
            item.not_all_valid = ko.computed(function(){
                return this.valid_count() < this.total_count();
            }, item);
        });
    }
});
