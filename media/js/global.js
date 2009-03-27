
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

function log(msg) {
    if (window.console) {
        console.log(msg);
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
        console.log(indent + name + ': ' + obj[name]);
        if (typeof obj[name] == 'object') {
            logobj(obj[name], indent + '  ');
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
    return $.browser.msie() && $.browser.version.string().substr(0, 1) == "7";
}

// Check if browser is Firefox 3.0
function browserIsFirefox30() {
    /*log('browserIsFirefox30()');
    log('$.browser.firefox(): ' + $.browser.firefox());
    log('$.browser.version.string(): ' + $.browser.version.string());*/
    return $.browser.firefox() && $.browser.version.string().substr(0,3) == "3.0";
}

// Check if browser is Safari 3
function browserIsSafari3() {
    return $.browser.safari() && $.browser.version.string().substr(0,1) == "3";
}

function isCompatibleBrowser() {
    //alert('isCompatibleBrowser()');
    //alert('navigator.userAgent: ' + navigator.userAgent);
    //alert('navigator.vendor: ' + navigator.vendor);
    //alert('$.browser.browser(): ' + $.browser.browser());
    //alert('$.browser.version.string(): ' + $.browser.version.string());
    //alert('$.browser.version.number(): ' + $.browser.version.number());
    
    return browserIsFirefox30() || browserIsIe7() || browserIsSafari3();
}

$(function() {
    // Show browser compatibility warning
    /*
    if (!isCompatibleBrowser()) {
        $('html').css('height', '100%');
        $('body').css('height', '100%');
        $('html').css('overflow', 'hidden');
        showBrowserWarning();
    }
    */
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




