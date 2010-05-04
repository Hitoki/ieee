
/*
function log(msg) {
    if (window.console) {
        console.log(msg);
    }
}

function error(msg) {
    alert(msg);
    return false;
}
*/

function listAppend(list, item) {
    if ($.trim(list) == '')
        return item;
    else
        return list + '|' + item;
}

function listFind(list, item) {
    list = list.split('|')
    for (var i=0; i<list.length; i++) {
        if (list[i] == item) {
            return i;
        }
    }
    return null;
}

function listRemove(list, item) {
    var i = listFind(list, item);
    if (i != null) {
        list = list.split('|');
        list.splice(i, 1);
        return list.join('|');
    }
    return list;
}

function listRemoveByIndex(list, i) {
    if (i != null) {
        list = list.split('|');
        list.splice(i, 1);
        return list.join('|');
    }
    return list;
}

function stripTags(text) {
    return text.replace( /<[^<>]*>/g, '' );
}

function sortTable(table, columnIndexes, order, headerRows) {
    table = $(table);
    
    if (headerRows == undefined)
        headerRows = 0;
    
    if (!(columnIndexes instanceof Array)) {
        columnIndexes = [columnIndexes];
    }
    
    var tbody = $(table.children('tbody')[0]);
    
    for (var i=headerRows; i<tbody.children('tr').length-1; i++) {
        for (var j=i+1; j<tbody.children('tr').length; j++) {
            var row1 = $(tbody.children('tr')[i]);
            var cols1 = row1.children('td');
            var col1 = $(cols1[columnIndexes[0]]);
            
            var row2 = $(tbody.children('tr')[j]);
            var cols2 = $(row2).children('td');
            var col2 = $(cols2[columnIndexes[0]]);
            
            if (order == 'ascending' && (stripTags(col1.html()) > stripTags(col2.html()))) {
                swapRows(table, row1, row2);
                
            } else if (order == 'descending' && (stripTags(col1.html()) < stripTags(col2.html()))) {
                swapRows(table, row1, row2);
                
            }
            /*else if (stripTags(col1.html()) == stripTags(col2.html()) && columnIndexes.length > 1) {
                // TODO: secondary sort
                console.log('  secondary sort');
                col1b = $(cols1[columnIndexes[1]]);
                col2b = $(cols2[columnIndexes[1]]);
                console.log('    col1b.html(): ' + col1b.html());
                console.log('    col2b.html(): ' + col2b.html());
                if (order == 'ascending' && col1b.html() > col2b.html()) {
                    swapRows(table, row1, row2);
                } else if (order == 'descending' && col1b.html() < col2b.html()) {
                    swapRows(table, row1, row2);
                }
                
            }*/
            
        }
        
    }
}

function arrayFind(array, value, field) {
    for (var i=0; i<array.length; i++) {
        if (array[i].field == value)
            return i;
    }
    return null;
}

function arrayAddAlpha(array, item, field) {
    for (var i=0; i<array.length; i++) {
        if (array[i][field] > item[field]) {
            break;
        }
    }
    
    array.splice(i, 0, item);
    return i;
}

function swapRows(tableElem, row1, row2) {
    var placeholder1 = $('<tr></tr>');
    row1.after(placeholder1);
    
    var placeholder2 = $('<tr></tr>');
    row2.after(placeholder2);
    
    placeholder1.before(row2);
    placeholder2.before(row1);
    
    placeholder1.remove();
    placeholder2.remove();
}

var KEYS = {
    tab: 9,
    enter: 13,
    escape: 27,
    left: 37,
    right: 39,
    up: 38,
    down: 40
}

////////////////////////////////////////////////////////////////////////////////

var multiSearches = [];

function MultiSearch(container, options) {
    var multiSearch = this;
    
    multiSearches.push(this);
    
    this.container = $(container);
    
    // Get the options
    this.options = extendExisting(
        {
            searchUrl: null,
            format: 'simple',
            showAsTable: true,
            sortCol: null,
            sortOrder: null,
            showCreateTagLink: false,
            society_id: null,
            society_tags_first: false,
            showSelectedOptions: true,
            excludeTagId: null,
            removeLinkFlyoverText: null
        },
        this.container.metadata(),
        options
    );
    
    // Validate options
    if (typeof this.options.searchUrl != 'string' || $.trim(this.options.searchUrl) == '')
        return error('MultiSearch(): must specify a "searchUrl"');
    
    if (typeof this.options.format != 'string' || (this.options.format != 'simple' && this.options.format != 'full_tags_table'))
        return error('MultiSearch(): format must be "simple" or "full_tags_table"');
    
    if (this.options.society_id != null)
        this.options.society_tags_first = true;
    
    /*
    // Prevent close popup if clicking within container... too big?
    this.container.click(function (e) {
        // Prevent clicks in the MultiSearch from propagating to the document.click() function below
        e.stopPropagation();
    });
    */
    
    // Events
    this.subscribers = {
        'preloaded_option': [],
        'added_option': [],
        'removed_option': [],
        'click_create_new_tag': []
    };
   
    this.container.data('multisearch', this);
    
    $(document).click(function(e) {
        // This only receives clicks that happened outside the MultiSearch... close the popup
        multiSearch.closePopup(true);
    });
    $(document).keydown(function(e) {
        // This only receives clicks that happened outside the MultiSearch... close the popup
        if (e.keyCode == KEYS.escape) {
            multiSearch.onKeyEscape(e);
        }
    });
    
    this.inputTimer = null;
    this.input = this.container.find('.multi-search-input');
    if (this.input.length == 0)
        return error('MultiSearch(): did not find .multi-search-input element');
    
    this.input.data('multisearch', this);
    this.input.keydown(function(e) {
        multiSearch.keydown(e);
    });
    this.input.click(function(e) {
        // Prevent clicks in the input box from propagating to the document.click() and closing the popup
        if (!multiSearch.popupVisible) {
            // Search for options when user clicks on the input box (if applicable)
            multiSearch.getOptionsValue = $(this).attr('value');
            multiSearch.getOptions($(this).attr('value'));
        }
        e.stopPropagation();
    });
    this.input.focus(function(e) {
        multiSearch._hideOtherMultiSearches();
    });
    
    this.dataElem = this.container.find('input.multi-search-data');
    if (this.dataElem.length == 0)
        return error('MultiSearch(): did not find any element "input.multi-search-data"');
    
    this.selectedOptionsElem = this.container.find('.multi-search-selected-options');
    if (this.selectedOptionsElem.length == 0)
        return error('MultiSearch(): did not find .multi-search-selected-options element');
    if (!this.options.showSelectedOptions) {
        this.selectedOptionsElem.hide();
    }
    
    
    if (this.options.showAsTable) {
        this.selectedOptionsTableElem = $('<table></table>').appendTo(this.selectedOptionsElem);
        if (this.options.format == 'full_tags_table') {
            this.selectedOptionsTableElem = $('<table class="tags"></table>').appendTo(this.selectedOptionsElem);
            
            // Grab the template and use it for the headers
            var template = $('#multisearch-tags-template');
            this.selectedOptionsTableElem.html(template.html());
            template.remove();
            
            this.selectedOptionsTableElem.find('a.multisearch-sort').each(function() {
                $(this).click(function() {
                    multiSearch.sort($(this).metadata().col, $(this).metadata().order);
                    return false;
                });
            });
        }
        
    } else {
        $('<br style="clear:both;"/>').appendTo(this.selectedOptionsElem);
    }
    
    this.getOptionsValue = null;
    this.selectedOptions = [];
    
    this.popupAnchorElem = this.container.find('.multi-search-popup-anchor');
    this.popupElem = $('<div class="multi-search-popup"></div>').appendTo(this.popupAnchorElem);
    this.popupElem.click(function(e) {
        // Prevent clicks in the popup from propagating to the document.click() and closing the popup
        e.stopPropagation();
    });
    
    
    // TODO: This works in IE7 but not Firefox
    this.popupElem.keydown(function(e) {
        multiSearch.keydown(e);
    });
    
    this.closePopup();
    
    // Load any pre-selected options (from the hidden input)
    var initialData = JSON.parse(this.dataElem.attr('value'));
    
    // Now add the preselected options
    for (var i=0; i<initialData.length; i++) {
        this.addSelectedOption(initialData[i], true);
    }
}

// Hide all other MultiSearches' dropdowns
MultiSearch.prototype._hideOtherMultiSearches = function() {
    for (var i=0; i<multiSearches.length; i++) {
        if (multiSearches[i] != this) {
            multiSearches[i].closePopup(true);
        }
    }
}

MultiSearch.prototype.keydown = function(e) {
    if (e.keyCode == KEYS.down) {
        this.onKeyDown(e);
    }
    else if (e.keyCode == KEYS.up) {
        this.onKeyUp(e);
    }
    else if (e.keyCode == KEYS.enter) {
        this.onKeyEnter(e);
    }
    else if (e.keyCode == KEYS.escape) {
        this.onKeyEscape(e);
    }
    else if (e.keyCode == KEYS.tab) {
        // User is tabbing out of the widget
        this.closePopup(true);
    }
    else {
        //log('  e.which: ' + e.which);
        //log('  e.keyCode: ' + e.keyCode);
        //e.preventDefault();
        this.setInputTimer();
    }
}

MultiSearch.prototype.clearInputTimer = function() {
    if (this.inputTimer) {
        clearTimeout(this.inputTimer);
        this.inputTimer = null;
    }
}

MultiSearch.prototype.setInputTimer = function() {
    var multiSearch = this;
    this.clearInputTimer();
    this.inputTimer = setTimeout(function() { multiSearch.onInputTimer(); }, 100);
}

MultiSearch.prototype.clearGetOptionsTimer = function() {
    if (this.getOptionsTimer) {
        clearTimeout(this.getOptionsTimer);
        this.getOptionsTimer = null;
    }
}

MultiSearch.prototype.setGetOptionsTimer = function() {
    var multiSearch = this;
    this.clearGetOptionsTimer();
    this.getOptionsTimer = setTimeout(function() { multiSearch.onGetOptionsTimer(); }, 100);
}

MultiSearch.prototype.onInputTimer = function() {
    this.clearInputTimer();
    var value = this.input.attr('value');
    if ($.trim(value) != '') {
        // User has entered text, search for it
        this.getOptionsValue = value;
        this.getOptions(value);
    } else {
        // User has entered no text, close the popup and cancel any ajax
        this.closePopup();
    }
    
}

function url_encode(obj) {
    var data = '';
    for (var i in obj) {
        if (data != '')
            data += '&';
        data += escape(i) + '=' + escape(obj[i]);
    }
    return data;
}

// Update and display the search options popup, in case something has changed
MultiSearch.prototype.updatePopup = function() {
    this.closePopup();
    var value = this.input.attr('value');
    if ($.trim(value) != '') {
        // User has entered text, search for it
        this.getOptionsValue = value;
        this.getOptions(value);
    }
}

// Initiate getting searchOptions for the given value
MultiSearch.prototype.getOptions = function(value) {
    var multiSearch = this;
    if ($.trim(value).length >= 2 || ($.trim(value) == '*' && this.options.society_id != null)) {
        var data = {
            search_for: value
        }
        if (this.options.excludeTagId != null) {
            data.exclude_tag_id = this.options.excludeTagId;
        }
        if (value == '*') {
            // Searching for all this society's tags
            data.society_id = this.options.society_id;
        }
        $.getJSON(this.options.searchUrl, url_encode(data), function(data) { multiSearch.onGetOptions(data); });
        this.showPopupLoading();
    } else {
        this.closePopup();
    }
}

// Show a popup after loading the searchOptions
MultiSearch.prototype.onGetOptions = function(data) {
    var multiSearch = this;
    
    // Make sure we're only handling the latest ajax request (that matches this.getOptionsValue)
    if (data.search_for == this.getOptionsValue) {
        // Close & reset the popup
        this.closePopup();
        
        var foundExactMatch = false;
        
        // Add the new searchOptions to the popup
        if (data.options.length != 0) {
            // Add the options to the popup
            for (var i in data.options) {
                var checked = this.findSelectedOptionByValue(data.options[i].value) != null;
                
                var option;
                if (this.options.format == 'simple') {
                    option = {
                        name: data.options[i].name,
                        value: data.options[i].value,
                        societies: data.options[i].societies
                    }
                } else {
                    option = {
                        name: data.options[i].name,
                        name_link: data.options[i].name_link,
                        value: data.options[i].value,
                        tag_name: data.options[i].tag_name,
                        sector_names: data.options[i].sector_names,
                        num_societies: data.options[i].num_societies.toString(),
                        num_related_tags: data.options[i].num_related_tags.toString(),
                        num_filters: data.options[i].num_filters.toString(),
                        num_resources: data.options[i].num_resources.toString(),
                        societies: data.options[i].societies
                    }
                }
                option.checked = checked;
                this.addSearchOption(option);
                
                if (option.name.toLowerCase() == data.search_for.toLowerCase())
                    foundExactMatch = true;
            }
            
            if (data.more_results) {
                $('<div class="multi-search-more-results">Enter more characters to view the rest of the results...</div>').appendTo(this.popupElem);
            }
        }
        
        if (!this.options.society_tags_first && data.options.length == 0) {
            // No options found
            $("<div class='multi-search-no-results'>No results found.</div>").appendTo(this.popupElem);
            
        } else if (this.options.society_tags_first) {
            // Show "No options found" separately for society tags and other tags
            if (this.searchOptionsFirst.length == 0) {
                this.popupFirstElem.after($("<div class='multi-search-no-results'>No results found.</div>"));
            }
            if (this.searchOptionsSecond.length == 0) {
                this.popupSecondElem.after($("<div class='multi-search-no-results'>No results found.</div>"));
            }
        }
        
        //console.log('foundExactMatch: ' + foundExactMatch);
        
        // Add "Create tag" link at bottom
        if (this.options.showCreateTagLink && !foundExactMatch && data.search_for != '*') {
            var createTag = $('<div class=""><a href="#create_new_tag" class="">Create a new tag "' + data.search_for + '"</a></div>').appendTo(this.popupElem);
            createTag.click(function() {
                // Notify the parent window of the "Create new tag" event
                if (window.notify != undefined) {
                    window.notify('multisearch_create_new_tag', {
                        multisearch: multiSearch,
                        tag_name: data.search_for
                    });
                }
                multiSearch._notify('click_create_new_tag', {
                    tag_name: data.search_for
                });
                return false;
            });
        }
        
        this.showPopup();
    }
}

MultiSearch.prototype.showPopupLoading = function() {
    this.showPopup();
    this.popupElem.html('<div class="multi-search-popup-loading"><img src="/media/images/ajax-loader.gif" /></div>');
}

MultiSearch.prototype.addSearchOption = function(searchOption) {
    var multiSearch = this;
    
    // Create searchOption element
    searchOption.elem = $("<div class=\"multi-search-popup-item\"><img class='multi-search-popup-item-checkbox' src='/media/images/checkbox.png' />" + htmlentities(searchOption.name) + "</div>");
    
    if (this.options.society_tags_first) {
        var belongsToSociety = false;
        if (this.options.society_id != null) {
            for (var i=0; i<searchOption.societies.length; i++) {
                if (searchOption.societies[i].id == this.options.society_id) {
                    belongsToSociety = true;
                    break;
                }
            }
        }
        if (belongsToSociety) {
            searchOption.elem.appendTo(this.popupFirstElem);
            this.searchOptionsFirst.push(searchOption);
            this.searchOptions = this.searchOptionsFirst.concat(this.searchOptionsSecond);
        } else {
            searchOption.elem.appendTo(this.popupSecondElem);
            this.searchOptionsSecond.push(searchOption);
            this.searchOptions = this.searchOptionsFirst.concat(this.searchOptionsSecond);
        }
    } else {
        searchOption.elem.appendTo(this.popupElem);
        this.searchOptions.push(searchOption);
    }
    
    // TODO: What is this here for??
    //searchOption.elem.html(searchOption.elem.html());
    
    searchOption.elem.data('value', searchOption.value);
    // Toggle the search option when it's clicked
    searchOption.elem.click(function(e) {
        multiSearch.toggleSearchOption($(this).data('value'));
    });
    searchOption.checkboxElem = searchOption.elem.children('img.multi-search-popup-item-checkbox');
    if (searchOption.checked == undefined)
        searchOption.checked = false;
    //this.searchOptions.push(searchOption);
    
    if (searchOption.checked) {
        searchOption.checkboxElem.attr('src', '/media/images/checkbox_on.png');
    }
}

MultiSearch.prototype.onKeyDown = function(e) {
    if (this.popupVisible) {
        // Make sure we have searchOptions
        if (this.searchOptions.length) {
            // The popup is visilble and has options... move down
            e.preventDefault();
            
            var index;
            if (this.highlightedSearchOptionValue == null) {
                // No option is selected, start at the top
                index = 0;
            } else if (this.findSearchOptionIndex(this.highlightedSearchOptionValue) < this.searchOptions.length-1) {
                // A option is already highlighted and is not the last one; select the next one down
                index = this.findSearchOptionIndex(this.highlightedSearchOptionValue) + 1;
            } else {
                // The last option is selected, do nothing
                return;
            }
            
            this.highlightSearchOption(this.searchOptions[index].value);
        }
    } else {
        // Popup is not visible, show it if a search phrase has been entered
        if ($.trim(this.input.attr('value')) != '') {
            this.getOptionsValue = this.input.attr('value');
            this.getOptions(this.input.attr('value'));
        }
    }
}

// For when user presses the up arrow
MultiSearch.prototype.onKeyUp = function(e) {
    if (this.popupVisible) {
        // Make sure we have searchOptions
        if (this.searchOptions.length) {
            // The popup is visilble and has options... move up
            e.preventDefault();
            
            var index;
            if (this.highlightedSearchOptionValue == null) {
                // No option is selected, start at the bottom
                index = this.searchOptions.length - 1;
            } else if (this.findSearchOptionIndex(this.highlightedSearchOptionValue) > 0) {
                // A option is already highlighted and is not the first one; select the next one up
                index = this.findSearchOptionIndex(this.highlightedSearchOptionValue) - 1;
            } else {
                // The last option is selected, do nothing
                return;
            }
            
            this.highlightSearchOption(this.searchOptions[index].value);
        }
    } else {
        // Popup is not visible, show it if a search phrase has been entered
        if ($.trim(this.input.attr('value')) != '') {
            this.getOptionsValue = this.input.attr('value');
            this.getOptions(this.input.attr('value'));
        }
    }
}

MultiSearch.prototype.onKeyEnter = function(e) {
    e.preventDefault();
    if (this.popupVisible && this.highlightedSearchOptionValue != null) {
        // Toggle this searchOption
        this.toggleSearchOption(this.highlightedSearchOptionValue);
    }
}

MultiSearch.prototype.findSearchOption = function(value) {
    for (var i=0; i<this.searchOptions.length; i++) {
        if (this.searchOptions[i].value == value)
            return this.searchOptions[i];
    }
    return null;
}

MultiSearch.prototype.findSearchOptionIndex = function(value) {
    for (var i=0; i<this.searchOptions.length; i++) {
        if (this.searchOptions[i].value == value)
            return i;
    }
    return null;
}

MultiSearch.prototype.toggleSearchOption = function(value) {
    var searchOption = this.findSearchOption(value);
    if (searchOption == null)
        return error('MultiSearch.toggleSearchOption(): value "' + value + '" not found');
    
    if (searchOption.checked) {
        this.unselectSearchOption(value);
    } else {
        this.selectSearchOption(value);
    }
}

MultiSearch.prototype.highlightSearchOption = function(value) {
    var searchOption = this.findSearchOption(value);
    if (searchOption == null)
        return error('MultiSearch.highlightSearchOption(): value "' + value + '" not found');
    
    if (this.highlightedSearchOptionValue != null)
        // Unhighlight the previous option
        this.findSearchOption(this.highlightedSearchOptionValue).elem.removeClass('multi-search-popup-highlighted-item');
        
    // Highlight the option
    this.highlightedSearchOptionValue = value;
    searchOption.elem.addClass('multi-search-popup-highlighted-item');
    
    // Automatically scroll the popup when the user highlights an option out of view.
    if ((searchOption.elem.attr("offsetTop") + searchOption.elem.attr("offsetHeight")) > (this.popupElem.attr('offsetHeight') + this.popupElem.attr('scrollTop'))) {
        // Highlighted element was further down, scroll down
        this.popupElem.attr('scrollTop',
            searchOption.elem.attr("offsetTop") + searchOption.elem.attr("offsetHeight") - this.popupElem.attr('offsetHeight') + 1
        );
    }
    else if (searchOption.elem.attr("offsetTop") < this.popupElem.attr('scrollTop')) {
        // Highlighted element was further up, scroll up
        this.popupElem.attr('scrollTop',
            searchOption.elem.attr("offsetTop") - 1
        );
    }
}

MultiSearch.prototype.selectSearchOption = function(value) {
    var searchOption = this.findSearchOption(value);
    if (searchOption == null)
        return error('MultiSearch.selectSearchOption(): value "' + value + '" not found');
    
    searchOption.checkboxElem.attr('src', '/media/images/checkbox_on.png');
    searchOption.checked = true;
    
    // Add this option to the selected options
    
    if (this.options.format == 'full_tags_table') {
        this.addSelectedOption({
            name: searchOption.name,
            name_link: searchOption.name_link,
            value: searchOption.value,
            tag_name: searchOption.tag_name,
            sector_names: searchOption.sector_names,
            num_societies: searchOption.num_societies.toString(),
            num_related_tags: searchOption.num_related_tags.toString(),
            num_filters: searchOption.num_filters.toString(),
            num_resources: searchOption.num_resources.toString(),
            societies: searchOption.societies
        });
    } else {
        this.addSelectedOption({
            name: searchOption.name,
            value: searchOption.value
        });
    }
}

MultiSearch.prototype.unselectSearchOption = function(value) {
    var searchOption = this.findSearchOption(value);
    if (searchOption == null)
        return error('MultiSearch.unselectSearchOption(): value "' + value + '" not found');
    
    searchOption.checkboxElem.attr('src', '/media/images/checkbox.png');
    searchOption.checked = false;
    
    // Remove this option from the selected options
    this.removeSelectedOptionByValue(searchOption.value);
}

// Return the index of the option with 'value', or null if not found
MultiSearch.prototype.findSearchOptionByValue = function(value) {
    for (var i=0; i<this.searchOptions.length; i++) {
        if (this.searchOptions[i].value == value)
            return i;
    }
    return null;
}

// Return the index of the option with 'value', or null if not found
MultiSearch.prototype.findSelectedOptionByValue = function(value) {
    for (var i=0; i<this.selectedOptions.length; i++) {
        if (this.selectedOptions[i].value == value)
            return i;
    }
    return null;
}

MultiSearch.prototype.sort = function(col, order) {
    // Highlight the correct sort arrow
    var sortLinks = this.selectedOptionsTableElem.find('a.multisearch-sort');
    for (var i=0; i<sortLinks.length; i++) {
        var image = $($(sortLinks[i]).children('img')[0]);
        if ($(sortLinks[i]).metadata().col == col &&  $(sortLinks[i]).metadata().order == order) {
            image.attr('src', image.attr('src').replace('_inactive', '_active'));
        } else {
            image.attr('src', image.attr('src').replace('_active', '_inactive'));
        }
    }
    
    sortTable(this.selectedOptionsTableElem, [col, 0], order, 1);
    
    this.options.sortCol = col;
    this.options.sortOrder = order;
}

MultiSearch.prototype.addSelectedOption = function(option, preload) {
    // Add the selected option if it's not already selected
    var multiSearch = this;
    
    if (preload == undefined)
        preload = false;
    
    // Add the option if it doesn't already  exist
    if (this.findSelectedOptionByValue(option.value) == null) {
        
        if (this.options.showAsTable) {
            // Create a row in the table
            option.elem = $('<tr></tr>').appendTo(this.selectedOptionsTableElem);
            
            if (this.options.format == 'full_tags_table') {
                
                option.nameElem = $('<td class="first-item"></td>').appendTo(option.elem);
                var link = $('<a href=""></a>').appendTo(option.nameElem);
                link.attr('href', option.name_link);
                link.html(htmlentities(option.tag_name));
                
                var cell;
                cell = $('<td class="left-text"></td>').appendTo(option.elem);
                cell.html(htmlentities(option.sector_names));
                autoTruncate(cell, { length:40, flyover:true });
                
                cell = $('<td></td>').appendTo(option.elem);
                if(option.num_societies != 0){
                    cell.html(htmlentities(option.num_societies.toString()));
                }
                
                cell = $('<td></td>').appendTo(option.elem);
                if(option.num_filters != 0){
                    cell.html(htmlentities(option.num_filters.toString()));
                }
                
                cell = $('<td></td>').appendTo(option.elem);
                if(option.num_resources != 0){
                    cell.html(htmlentities(option.num_resources.toString()));
                }
                
                cell = $('<td></td>').appendTo(option.elem);
                if(option.num_related_tags != 0){
                    cell.html(htmlentities(option.num_related_tags.toString()));
                }
                
            } else {
                option.nameElem = $('<td class="small-tab-table"></td>').appendTo(option.elem);
                option.nameElem.html(htmlentities(option.name));
                
            }
            
            option.removeCellElem = $('<td><a href="#remove_' + option.value + '" class="remove-link">[x]</a></td>').appendTo(option.elem);
            option.removeLinkElem = option.removeCellElem.find('a');
            
            option.removeLinkElem.data('value', option.value);
            option.removeLinkElem.click(function(e) {
                // Remove the option when clicked
                multiSearch.removeSelectedOptionByValue($(this).data('value'));
                if (multiSearch.options.removeLinkFlyoverText != null) {
                    Flyover.hide();
                }
                return false;
            });
            if (this.options.removeLinkFlyoverText != null) {
                // Attach a flyover to the remove element
                Flyover.attach(option.removeLinkElem, {content:this.options.removeLinkFlyoverText});
            }
            
        } else {
            // Create a cloud item
            option.elem = $('<div class="multi-search-selected-option"></div>');
            // Insert the option before the <br> clearing tag
            this.selectedOptionsElem.children('br').before(option.elem);
            option.elem.html(htmlentities(option.name));
            option.elem.data('value', option.value);
            option.elem.click(function(e) {
                // Remove the option when clicked
                multiSearch.removeSelectedOptionByValue($(this).data('value'));
            });
        }
        
        var pos = arrayAddAlpha(this.selectedOptions, option, 'name');
        
        // Apply the current sort to the new item
        if (this.options.sortCol != null && this.options.sortOrder != null ) {
            this.sort(this.options.sortCol, this.options.sortOrder);
        }
        
        // Avoid rewriting the output element when we're just preloading the options (for performance)
        if (!preload) {
            // Add the value to the output element
            var data = JSON.parse(this.dataElem.attr('value'));
            if (this.options.format == 'full_tags_table') {
                data.push({
                    name: option.name,
                    name_link: option.name_link,
                    value: option.value,
                    tag_name: option.tag_name,
                    sector_names: option.sector_names,
                    num_societies: option.num_societies.toString(),
                    num_related_tags: option.num_related_tags.toString(),
                    num_filters: option.num_filters.toString(),
                    num_resources: option.num_resources.toString(),
                    societies: option.societies
                });
            } else {
                data.push({
                    name: option.name,
                    value: option.value
                });
            }
            this.dataElem.attr('value', JSON.stringify(data));
        }
    }
    
    // Notify the parent window if applicable
    if (preload) {
        if (window.notify != undefined) {
            window.notify('preloaded_multisearch_option', {
                multisearch: this,
                option: option
            });
        }
        this._notify('preloaded_option', {
            option: option
        });
    } else {
        if (window.notify != undefined) {
            window.notify('added_multisearch_option', {
                multisearch: this,
                option: option
            });
        }
        this._notify('added_option', {
            option: option
        });
    }
}

MultiSearch.prototype.removeSelectedOptionByValue = function(value) {
    // Remove the selected option if it exists
    var index = this.findSelectedOptionByValue(value);
    if (index != null) {
        this.selectedOptions[index].elem.remove();
        var option = this.selectedOptions[index];
        this.selectedOptions.splice(index, 1);
        
        // Remove the value from the output element
        var data = JSON.parse(this.dataElem.attr('value'));
        for (var i=0; i<data.length; i++) {
            if (data[i].value == value) {
                data.splice(i, 1);
                break;
            }
        }
        this.dataElem.attr('value', JSON.stringify(data));
    }
    
    // Notify the parent window if applicable
    if (window.notify != undefined) {
        window.notify('removed_multisearch_option', {
            multisearch: this,
            option: option
        });
    }
    this._notify('removed_option', {
        option: option
    });
}

MultiSearch.prototype.onKeyEscape = function(e) {
    if (this.popupVisible) {
        // Close the popup & reset options
        e.preventDefault();
        this.closePopup(true);
    }
}

// Shows the popup element
MultiSearch.prototype.showPopup = function() {
    if (!this.popupVisible) {
        // Show popup
        this.popupVisible = true;
        this.popupElem.show();
        var height = this.input.attr('offsetHeight') - 3;
        this.popupElem.css('top', height + 'px');
        var width = this.input.attr('offsetWidth') - 3;
        this.popupElem.css('width', width + 'px');
    }
}

// Hides & clears the popup element, and resets all popup data
MultiSearch.prototype.closePopup = function(clear_value) {
    var multisearch = this;
    if (clear_value == undefined)
        clear_value = false;
    
    if (this.popupVisible && clear_value) {
        // NOTE: Simply setting this.input.attr('value', '') here does not work (it's immediately overwritten with the original value).
        setTimeout(function() {
            multisearch.clearValue();
        }, 10);
    }
    // Close the popup & reset options
    this.popupVisible = false;
    this.popupElem.html('');
    if (this.options.society_tags_first) {
        this.popupFirstElem = $('<div><div class="multi-search-popup-first">This Society&#39;s Tags:</div></div>').appendTo(this.popupElem);
        this.popupSecondElem = $('<div><div class="multi-search-popup-second">Other Tags:</div></div>').appendTo(this.popupElem);
    }
    this.popupElem.hide();
    this.searchOptions = [];
    this.searchOptionsFirst = [];
    this.searchOptionsSecond = [];
    
    this.highlightedSearchOptionValue = null;
    this.getOptionsValue = null;
}

MultiSearch.prototype.clearValue = function() {
    this.input.attr('value', '');
    this.input.blur();
}

// Gets the number of selected options
MultiSearch.prototype.getNumSelectedOptions = function() {
    return this.selectedOptions.length;
}


// Allows another object to subscribe to this object's events.
// @param event - the name of the event.
// @param func - the callback function.  Will be called like:
//   func([source_object], [event_name], [optional_event_data]);
// 
MultiSearch.prototype.subscribe = function(event, func) {
    if (!event in this.subscribers) {
        alert('MultiSearch.subscribe(): Unknown event "' + event + '"');
        return;
    }
    this.subscribers[event].push(func);
},

// Notify all subscribers of an event.
MultiSearch.prototype._notify = function(event, data) {
    if (!event in this.subscribers) {
        alert('MultiSearch.notify(): Unknown event "' + event + '"');
        return;
    }
    for (var i=0; i<this.subscribers[event].length; i++) {
        var func = this.subscribers[event][i];
        func(this, event, data);
    }
}

////////////////////////////////////////////////////////////////////////////////

function attachMultiSearches(elem) {
    elem = $(elem);
    elem.find('.multi-search').each(function() {
        new MultiSearch(this);
    });
}

$(function() {
    $('.multi-search').each(function() {
        new MultiSearch(this);
    });
}); 