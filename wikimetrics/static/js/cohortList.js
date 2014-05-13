$(document).ready(function(){
    
    var viewModel = {
        filter: ko.observable(''),
        cohorts: ko.observableArray([]),
        
        populate: function(cohort, data){
            cohort.validated(data.validated);
            cohort.validated_count(data.validated_count);
            cohort.valid_count(data.valid_count);
            cohort.invalid_count(data.invalid_count);
            cohort.total_count(data.total_count);
            cohort.validation_status(data.validation_status);
            cohort.wikiusers(data.wikiusers);
            cohort.delete_message(data.delete_message);
            this._populateTags(cohort, data)
        },
        
        _populateTags: function(cohort,data){
            cohort.tags(data.tags);
            cohort.tagsForMatching  = []
            data.tags.forEach(function(item){
                cohort.tagsForMatching.push(item.name)
            })
            
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
        
        addTag: function(form){
            /*
            * turns tag lowercase and replaces ' ' with '-'
            */
            function parseTag(tag){
                return tag.replace(/\s+/g, "-").toLowerCase()
            }
            
            var cohort = this;
            var tag = cohort.tag_name();
            tag = parseTag(tag)
            //Make sure match is exact
            var existing = cohort.tagsForMatching.indexOf(tag) >= 0;
            if (!existing){
                $.post('/cohorts/' + cohort.id + '/tag/add/' + tag)
                    .done(site.handleWith(function(data){
                        if(data.exists){
                            site.showWarning('A similar tag already exists on this cohort');
                        }
                        else{
                            viewModel._populateTags(cohort, data);
                        }
                    }))
                    .fail(site.failure);
            } else {
                var matches = $('.tags span.label span:contains("' + tag + '")');
                matches.addClass('highlight');
                setTimeout(function(){
                    matches.removeClass('highlight');
                }, 1500);
            }
            cohort.tag_name('');
        },
        
        deleteTag: function(event, cohort, tag){
            $.post('/cohorts/' +  cohort.id + '/tag/delete/' + tag.id)
                .done(site.handleWith(function(data){
                    cohort.tags.remove(tag);
                    cohort.tagsForMatching.splice(
                        cohort.tagsForMatching.indexOf(tag.name),1)
                    
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
        bareList = ko.utils.unwrapObservable(list);
        ko.utils.arrayForEach(bareList, function(item){
            // TODO: auto-map the new properties
            item.wikiusers = ko.observableArray([]);
            item.validated = ko.observable(false);
            item.validated_count = ko.observable(0);
            item.invalid_count = ko.observable(0);
            item.valid_count = ko.observable(0);
            item.total_count = ko.observable(0);
            item.validation_status = ko.observable();
            item.delete_message = ko.observable();
            item.tag_name = ko.observable();
            item.tags = ko.observableArray([]);
        });
    }
});
