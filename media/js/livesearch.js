
function LiveSearch(inputElem) {
    log('LiveSearch()');
    var liveSearch = this;
    inputElem = $(inputElem);
    
    // Options
    
    this.options = {
        'url': null,
        'use_tags_callback': false,
        'search_on_page_load': false
    };
    this.options = $.extend(this.options, inputElem.metadata());
    
    // Validate options
    
    if (!this.options.use_tags_callback) {
        if (this.options.url == null || $.trim(this.options.url) == '') {
            alert('Error in LiveSearch(): url is blank.');
            return;
        }
    }
    
	// The last known searchFor value, so we can tell if the input value has changed.
    this.lastValue = null;
	// The phrase currently being searched for.
    this.searchingFor = null;
    
    this.inputElem = $(inputElem);
    this.inputElem.change(function() {
        liveSearch.update();
    });
    this.inputElem.keyup(function() {
        liveSearch.update();
    });
    
    if (this.options.search_on_page_load) {
        // When page loads, use the intial value
        this.update();
    } else {
        // Ignore & erase the initial value
        this.inputElem.val('');
        this.lastValue = this.inputElem.val();
    }
}

LiveSearch.prototype.update = function(useDelayValue) {
    log('LiveSearch.update()');
    var liveSearch = this;
    var value = this.inputElem.val();
	log('  value: ' + value);
	log('  useDelayValue: ' + useDelayValue);
	log('  this.lastValue: ' + this.lastValue);
	// Check if the value has changed, or the delay has expired for this value.
    if (value != this.lastValue || value == useDelayValue) {
        
		if (value.length == 2 && value != useDelayValue) {
			// Found a new 2 char value, set the delay timer.
			log('Found a new 2 char value "' + value + '", setting delay timer.');
			setTimeout(
				function() {
					liveSearch.update(value);
				},
				750
			);
			
		} else if (
			value.length != 2 || 
			(value.length == 2 && value == useDelayValue)
		) {
			// Value was > 3 chars, or the delay for this 2-char value has expired.
			log('Searching for "' + value + '"');
			
			// Do the search
			if (this.options.use_tags_callback) {
				log('calling callback');
				
				if (this.searchingFor != null) {
					log('Already searching!');
				} else {
					
					this.searchingFor = value;
					
					if (window.Tags == undefined) {
						alert('Error in LiveSearch.update(): Tags is not defined.')
						return;
					}
					
					Tags.showSearchResults(value, function(searchFor, data) {
						liveSearch.onUpdate(searchFor, data);
					});
				}
				
			} else {
				log('calling ajax url');
				$.ajax({
					url: this.options.url,
					data: {
						search_for: value
					},
					//dataType: 'json',
					dataType: 'html',
					success: function(data) {
						liveSearch.onResults(data);
					}
				});
			}
		} else {
			log('Ignoring "' + value + '"');
		}
		
		this.lastValue = value;
	}
}

LiveSearch.prototype.onUpdate = function(searchFor, data) {
    log('LiveSearch.onUpdate(): received page for "' + searchFor + '"');
	if (searchFor == this.searchingFor) {
		log('clearing searchingFor');
		this.searchingFor = null;
		this.update();
	}
}

LiveSearch.prototype.onResults = function(data) {
    if (this.popupElem) {
        //this.popupElem.empty();
    } else {
        this.popupElem = $('<div></div>').insertAfter(this.inputElem);
    }
    
    this.popupElem.html(data);
    
    ////this.popupElem;
    //log('onResults()');
    //log('data: ' + data);
    //log('data.search_for: ' + data.search_for);
    //var search_for = data.search_for;
    //log('data.results: ' + data.results);
    //log('data.results.length: ' + data.results.length);
    //
    //var str = '';
    //str += '<p>';
    //str += 'Showing ' + data.results.length + ' out of ' + data.total_num_tags + ' results.';
    //str += '</p>';
    //str += '<ul>';
    //for (var i=0; i<data.results.length; i++) {
    //    //log('data.results[' + i + ']: ' + data.results[i]);
    //    //log('data.results[' + i + '].name: ' + data.results[i].name);
    //    
    //    var name = data.results[i].name;
    //    //name = name.replace(search_for, '<u>' + search_for + '</u>');
    //    name = name.replace(new RegExp('(' + search_for + ')', 'i'), '<u>$1</u>');
    //    str += '<li>' + name + '</li>';
    //}
    //str += '</ul>';
    //
    //this.popupElem.html(str);
}

function attachLiveSearches(elem) {
    $(elem).find('.live-search').each(function() {
        new LiveSearch(this);
    });
}

$(function() {
    attachLiveSearches(document);
});
