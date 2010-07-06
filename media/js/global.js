
function implode(glue, array) {
    var str = "";
    for (var i=0; i<array.length; i++) {
        if (i)
            str += glue + array[i];
        else
            str += array[i];
    }
    return str;
}

/*
function log(name, value, print, indent, first) {
    if (print == undefined)
        print = true;
    if (indent == undefined)
        indent = "";
    if (first == undefined)
        first = false;
    
    var result = "";
    if (typeof value == 'object') {
        result += indent + name + ": {\n";
        var first = true;
        for (var i in value) {
            if (first)
                result += log(i, value[i], false, indent + "  ", first) + "\n";
            else
                result += log(i, value[i], false, indent + "  ", first) + "\n";
            first = false;
        }
        result += indent + "}";
    } else if (typeof value == 'string') {
        result += indent + name + ": \"" + value.replace('"', '\\"') + "\"";
    } else {
        result += indent + name + " (" + (typeof value) + "): " + value;
    }
    
    if (print) 
        console.log(result);
    else
        return result;
}
*/

var logStartTime = null;

function log(msg) {
    if (window.console) {
        if (logStartTime == null)
            logStartTime = new Date() / 1000;
        var seconds = (new Date() / 1000) - logStartTime;
        console.log(seconds.toFixed(1) + ': ' + msg);
    }
}

function error(msg) {
    alert(msg);
    return false;
}

function logobj(obj, indent) {
    if (indent == undefined)
        indent = '';
    for (name in obj) {
        try {
            log(indent + name + ': ' + obj[name]);
        } catch (e) {
            log(indent + name + ': (Error getting value)');
        }
        try {
            if (typeof obj[name] == 'object') {
                logobj(obj[name], indent + '  ');
            }
        } catch (e) {
            // do nothing
        }
        
    }
}

// Similar to jQuery's $.extend(), except it only overwrites exising vars in obj1 with obj2 values
function extendExisting() {
    var args = extendExisting.arguments;
    
    if (!args[0])
        args[0] = {};
    
    for (var argnum=1; argnum<args.length; argnum++) {
        if (args[argnum]) {
            for (var i in args[0]) {
                if (i in args[argnum]) {
                    args[0][i] = args[argnum][i];
                }
            }
        }
    }
    
    return args[0];
}

function showBrowserWarning() {
    warning = $('<div class="browser-warning"></div>').appendTo('body');
    warning.load('/browser_warning');
}

function isCompatibleBrowser() {
    //alert('isCompatibleBrowser()');
    //alert('navigator.userAgent: ' + navigator.userAgent);
    //alert('navigator.vendor: ' + navigator.vendor);
    //alert('$.browser.browser(): ' + $.browser.browser());
    //alert('$.browser.version.string(): ' + $.browser.version.string());
    //alert('$.browser.version.number(): ' + $.browser.version.number());
    
    var v = $.browser.version.number();
    return (
    	( $.browser.msie    && v >= 7 ) ||
    	( $.browser.firefox && v >= 3 ) ||
		( $.browser.safari  && v >= 4 ) ||
		( $.browser.chrome  && v >= 4 )
    );
}

function setBrowserCookie() {
    $('.browser-warning').remove();
    //set a cookie to show that the user has skipped the warning
    var options = { path: '/', expires: 1 };
    $.cookie("ignoreWarning", 'ignore', options);
}

$(function() {

    // get browser compatibility cookie
    var browser_cookie = $.cookie("ignoreWarning");
    
    // Show browser compatibility warning
    if ( browser_cookie != 'ignore' && !isCompatibleBrowser()) {
        $('html').css('height', '100%');
        $('body').css('height', '100%');
        $('html').css('overflow', 'hidden');
        showBrowserWarning();
    }
    
});

// Append a string to the end of a URL, before the #hash
function urlAppend(url, str) {
    if (/#/.test(url)) {
        return url.replace('#', str + '#');
    } else {
        return url + str;
    }
}

function urlGetHash(url) {
    var matches = url.match(/#.+/);
    if (matches)
        return matches[0];
    else
        return '';
}

function urlRemoveHash(url) {
    return url.replace(/#.+/, '');
}

// 

function HighlightCheckbox(elem, options) {
    var highlightcheckbox = this;
    this.elem = $(elem);
    this.options = $.extend(
        {
            highlightElem: null
        },
        this.elem.metadata(),
        options
    );
    
    if (this.options.highlightElem == null) {
        // Attempt to find the label
        var id = this.elem.attr('id');
        var label = null;
        $('label').each(function() {
            if ($(this).attr('for') == id)
                label = $(this);
        });
        if (label != null)
            this.options.highlightElem = label
    } else {
        this.options.highlightElem = $(this.options.highlightElem);
    }
    
    if (this.options.highlightElem == null) {
        alert('HighlightCheckbox(): Error, this.options.highlightElem must be specified.');
        return;
    }
    
    this.elem.change(function(e) {
        highlightcheckbox.onChange(e);
    });
    
    this.elem.click(function(e) {
        highlightcheckbox.onChange(e);
    });
    
    this.onChange();
}

HighlightCheckbox.prototype.onChange = function (e) {
    if (this.elem.attr('checked')) {
        var classes = this.options.highlightElem.attr('className').split(' ');
        for (var i=0; i<classes.length; i++) {
            if (classes[i].substr(classes[i].length-10, 10) != '_highlight') {
                this.options.highlightElem.addClass(classes[i] + '_highlight');
            }
        }
    } else {
        var classes = this.options.highlightElem.attr('className').split(' ');
        for (var i=0; i<classes.length; i++) {
            if (classes[i].substr(classes[i].length-10) == '_highlight') {
                this.options.highlightElem.removeClass(classes[i]);
            }
        }
    }
}

function attachHighlightCheckboxes(elem) {
    if (elem) {
        elem.find('.highlight-checkbox').each(function() {
            new HighlightCheckbox(this);
        });
    } else {
        $('.highlight-checkbox').each(function() {
            new HighlightCheckbox(this);
        });
    }
}

//

function attachSelectCheckboxOnClick(elem) {
    elem = $(elem);
    elem.find('.select-checkbox-on-click').click(function() {
        $(this).find('input[type="checkbox"]').click();
        $(this).find('input[type="checkbox"]').change();
    });
    elem.find('.select-checkbox-on-click input[type="checkbox"]').click(function(e) {
        // Stop propagation to above function, otherwise checkbox is clicked twice & doesn't change
        e.stopPropagation();
    });
}

function attachItemsPerPage(elem) {
    if (elem == undefined) {
        elem = $('body');
    }
    
    elem.find('select.items-per-page').change(function() {
        // Can't use a simple this.form.submit() here, since IE7 removes the hash from the URL (!).
        var urlbits = this.form.action.split('#');
        if (urlbits.length > 1) {
            var url = urlbits[0];
            var hash = '#' + urlbits[1];
        } else {
            var url = urlbits[0];
            var hash = '';
        }
        var queryvars = {};
        for (var i=0; i<this.form.elements.length; i++) {
            var element = this.form.elements[i];
            queryvars[element.name] = element.value;
        }
        
        var querystring = '';
        for (var i in queryvars) {
            if (querystring != '') {
                querystring += '&';
            }
            querystring += i + '=' + escape(queryvars[i]);
        }
        if (querystring != '') {
            querystring = '?' + querystring;
        }
        
        var fullurl = url + querystring + hash
        
        window.location = fullurl;
    });    
}

function attachSocietyLogoFlyovers(elem) {
    elem.find('img.logo-flyover').each(function() {
        Flyover.attach(this, {
            content_html: "<img src=\"" + $(this).metadata().full_url + "\" />"
        });
    });
}

function attachOtherConferencesToggle(elem) {
    elem.find('a.show-other-conferences, a.hide-other-conferences').each(function() {
        $(this).click(function() {
            $('#other-conferences-' + $(this).metadata().id).toggle();
            $('#show-other-conferences-' + $(this).metadata().id).toggle();
            $('#hide-other-conferences-' + $(this).metadata().id).toggle();
            return false;
        });
    });
}

function attachExpandSeries(elem) {
    elem.find('tr.current-conference').each(function() {
        var expandSeries = new ExpandSeries(this);
    });
}

function attachCopyTags(elem) {
    // Attach handlers to the "copy tags" links
    elem.find('a.copy-tags-to-clipboard').click(function() {
        var resourceId = $(this).metadata().resourceId
        var linkElem = this;
        $.ajax({
            url: INDEX_URL + 'admin/ajax/copy_resource_tags',
            data: {
                resource_id: resourceId
            },
            type: 'POST',
            success: function(data) {
                onCopyTagsSuccess(linkElem, data);
            }
        });
        
        return false;
    });
    
    // Attach handlers to the "paste tags" links
    elem.find('a.paste-tags').click(function() {
        var resourceId = $(this).metadata().resourceId;
        Lightbox.show(INDEX_URL + 'admin/ajax/paste_resource_tags?resource_id=' + resourceId, { customClass: 'paste-tags' });
        return false;
    });
}

// Called when an AJAX request has copied the tags, change the link text to show the status
function onCopyTagsSuccess(linkElem, data) {
    $(linkElem).html('<img src="' + MEDIA_URL + 'images/copy_to_clipboard_checked.png" /> Tags copied to clipboard');
    $(linkElem).hide();
    $(linkElem).fadeIn();
}

function resizeLightboxTab() {
    var windowHeight = $(window).height();
    $('.resources-lightbox-content').css('height', windowHeight - 200);
    $('#resource-tabs .nootabs-selected-tab').css('height', windowHeight - 320);
    $('.nootabs-selected-tab div.group').css('height', windowHeight - 350);
}

function addCommas(nStr) {
    // From http://www.mredkj.com/javascript/nfbasic.html, public domain
	nStr += '';
	x = nStr.split('.');
	x1 = x[0];
	x2 = x.length > 1 ? '.' + x[1] : '';
	var rgx = /(\d+)(\d{3})/;
	while (rgx.test(x1)) {
		x1 = x1.replace(rgx, '$1' + ',' + '$2');
	}
	return x1 + x2;
}

// This loads the xplore results for a tag into the given element via AJAX.
function getXploreResults(elem, showAll, offset) {
    if (showAll == undefined) {
        showAll = false;
    }
    if (offset == undefined) {
        offset = 0;
    }
    
    var elem2 = $(elem);
    var tagId = elem2.metadata().tagId;
    elem2.html('<div class="loading"><img src="/media/images/ajax-loader.gif" class="loading" /><br/>Loading Xplore results...</div>');
    var ajax = $.ajax({
        url: '/ajax/xplore_results',
        data: {
            tag_id: tagId,
            show_all: showAll,
            offset: offset
        },
        type: 'post',
        success: function(data) {
            //log('success...');
            elem2.html(data);
            //log('  elem2: ' + elem2);
            //log('  elem2.length: ' + elem2.length);
            //log('  elem2[0]: ' + elem2[0]);
            //log('  elem2[0].nodeName: ' + elem2[0].nodeName);
            var num = elem2.find('#num-xplore-results-hidden').html();
            $('#num-xplore-results').text('(' + num + ')');
            
            // NOTE: Need to get rid of the comma, or we get bad numbers.
            num = num.replace(',', '');
            var numRelatedItems = parseInt($('#num-related-items').metadata().number);
            $('#num-related-items').text(addCommas(numRelatedItems + parseInt(num)));
            
            elem2.find('#xplore-view-previous').click(function() {
                getXploreResults(elem, false, offset-10);
                return false;
            });
            
            elem2.find('#xplore-view-next').click(function() {
                getXploreResults(elem, false, offset+10);
                return false;
            });
            
            resizeLightboxTab();
            
        }
    });
    elem2.data('ajax', ajax);
}

function attachXploreResults(elem) {
    getXploreResults(elem);
}

// Call elem whenever new content is created dynamically to attach any scripts
function attachScripts(elem) {
    elem = $(elem);
    attachBlurTexts(elem);
    attachAutoTruncates(elem);
    attachFlyovers(elem);
    attachLightboxes(elem);
    attachMultiSearches(elem);
    attachNootabs(elem);
    attachSelectCheckboxOnClick(elem);
    attachItemsPerPage(elem);
    attachSocietyLogoFlyovers(elem);
    attachOtherConferencesToggle(elem);
    attachExpandSeries(elem);
    attachCopyTags(elem);
}

function openIEEEtv(URL){
	newWindow = window.open(URL,"ieeeTV","scrollbars=no,resizable=no,HEIGHT=624,WIDTH=982");
	newWindow.focus();
}

var mouseX = null;
var mouseY = null;

$(function() {
    log('global.js');
    
    $('.select-checkbox-on-click').click(function() {
        $(this).find('input[type="checkbox"]').click();
        $(this).find('input[type="checkbox"]').change();
    });
    $('.select-checkbox-on-click input[type="checkbox"]').click(function(e) {
        // Stop propagation to above function, otherwise checkbox is clicked twice & doesn't change
        e.stopPropagation();
    });
    
    attachHighlightCheckboxes();
    attachItemsPerPage();
    
    // Bind a callback to any AJAX error (to prevent silent fails).
    $('body').bind(
        'ajaxError',
        function (event, XMLHttpRequest, textStatus, errorThrown) {
            
            // Show the error as a DHTML popup
            Lightbox.hide();
            Flyover.hide();
            
            var divElem = $('<div></div>').appendTo('body');
            divElem.css('position', 'absolute');
            divElem.css('margin', '1em');
            divElem.css('padding', '1em');
            divElem.css('background', 'white');
            divElem.css('border', '1px solid black');
            divElem.css('top', '0');
            divElem.css('left', '0');
            divElem.html(XMLHttpRequest["responseText"]);
            
            // Log the error
            log('-- AJAX ERROR: --------------------');
            log(XMLHttpRequest["responseText"].substr(0, 200));
            log('-----------------------------------');
        }
    );
    
    // Bind society logo flyovers
    attachSocietyLogoFlyovers($(document));
    
    attachOtherConferencesToggle($(document));
    
    setTimeout(function() {
        attachExpandSeries($(document));
    }, 500);
    
    attachCopyTags($(document));
	
	// Keep track of the mouse's position
	$().mousemove(function(e) {
		mouseX = e.pageX;
		mouseY = e.pageY;
	}); 

});
