
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

// Check if browser is IE7
function browserIsIe7() {
    return $.browser.msie && $.browser.version.string().substr(0, 1) == "7";
}

// Check if browser is IE7
function browserIsIe8() {
    return $.browser.msie && $.browser.version.string().substr(0, 1) == "8";
}

// Check if browser is Firefox 3.0
function browserIsFirefox30() {
    /*log('browserIsFirefox30()');
    log('$.browser.firefox(): ' + $.browser.firefox());
    log('$.browser.version.string(): ' + $.browser.version.string());*/
    return $.browser.firefox && $.browser.version.string().substr(0,3) == "3.0";
}

// Check if browser is Firefox 3.5
function browserIsFirefox35() {
    return $.browser.firefox && $.browser.version.string().substr(0,3) == "3.5";
}

// Check if browser is Safari 3
function browserIsSafari3() {
    return $.browser.safari && $.browser.version.string().substr(0,1) == "3";
}

// Check if browser is Safari 4
function browserIsSafari4() {
    return $.browser.safari && $.browser.version.string().substr(0,1) == "4";
}

function isCompatibleBrowser() {
    //alert('isCompatibleBrowser()');
    //alert('navigator.userAgent: ' + navigator.userAgent);
    //alert('navigator.vendor: ' + navigator.vendor);
    //alert('$.browser.browser(): ' + $.browser.browser());
    //alert('$.browser.version.string(): ' + $.browser.version.string());
    //alert('$.browser.version.number(): ' + $.browser.version.number());
    
    return browserIsFirefox30() || browserIsFirefox35() || browserIsIe7() || browserIsIe8() || browserIsSafari4();
}

$(function() {
    // Show browser compatibility warning
    if (!isCompatibleBrowser()) {
        $('html').css('height', '100%');
        $('body').css('height', '100%');
        $('html').css('overflow', 'hidden');
        showBrowserWarning();
    }
});


function FormatUrl(elem) {
    var formatUrl = this;
    this.elem = $(elem);
    this.elem.change(function() {
        formatUrl.update();
    });
    this.elem.blur(function() {
        formatUrl.update();
    });
}

FormatUrl.prototype.update = function() {
    var value = this.elem.attr('value');
    if (!/^http:\/\//.test(value) && !/^https:\/\//.test(value)) {
        value = 'http://' + value;
        this.elem.attr('value', value);
    }
}

$(function () {
    $('#id_url').each(function() {
        new FormatUrl(this);
    });
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

// Call this whenever new content is created dynamically to attach any scripts
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
}

$(function() {
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

});

