
function LiveUrl() {
    this.elems = [];
    this.timer = null;
    this.href = null;
}

LiveUrl.prototype.add = function(elem) {
    var liveUrl = this;
    elem = $(elem);
    if (elem.attr('nodeName') != 'A')
        return error('LiveUrl.add(): elem is not an A element.');
    this.elems.push(elem);
    
    if (!this.timer) {
        this.timer = setTimeout(function() { liveUrl.update(); }, 500);
    }
}

function parseUrl(url) {
    //log('parseUrl()');
    //log('  url: ' + url);
    
    var result = {};
    
    result.url = url;
    
    var temp = url.match(/^([^?]+)(.+)$/);
    result.base = temp[1];
    var query = temp[2];
    result.queryVars = {};
    //log('  result.base: ' + result.base);
    //log('  result.query: ' + result.query);
    
    if (query.length > 0) {
        var pairs = query.substr(1, query.length-1).split('&');
        for (var i=0; i<pairs.length; i++) {
            var bits = pairs[i].split('=');
            result.queryVars[bits[0]] = unescape(bits[1]);
            //log('  name: ' + bits[0]);
            //log('  value: ' + bits[1]);
        }
    }
    return result;
}

function buildUrl(obj) {
    var result = obj.base;
    var queryString = '';
    for (var i in obj.queryVars) {
        if (queryString != '')
            queryString += '&';
        queryString += i + '=' + escape(obj.queryVars[i]);
    }
    if (queryString != '')
        result += '?' + queryString;
    return result;
}

function changeQueryVar(url, varName, value) {
    //log('changeQueryVar()');
    var obj = parseUrl(url);
    //log('  url: ' + url);
    
    obj.queryVars[varName] = value;
    
    var url2 = buildUrl(obj);
    //log('  url2: ' + url2);
    
    //log('~changeQueryVar()');
    return url2;
}

LiveUrl.prototype.update = function() {
    var liveUrl = this;
    clearTimeout(this.timer);
    // Check if the URL has changed
    if (this.href != window.location.href) {
        // URL has changed, update all the live links
        for (var i=0; i<this.elems.length; i++) {
            var options = $.extend({
                varName: 'url'
                },
                this.elems[i].metadata()
            );
            
            //log('  options.varName: ' + options.varName);
            
            //log("  this.elems[i].attr('href'): " + this.elems[i].attr('href'));
            var newHref = changeQueryVar(this.elems[i].attr('href'), options.varName, window.location.href);
            //log("  newHref: " + newHref);
            this.elems[i].attr('href', newHref);
            
            
            /*
            var href = window.location.href;
            // Replace the hash with the current one
            if (this.elems[i].metadata().hashOnly != undefined) {
                href = urlRemoveHash(this.elems[i].attr('href')) + urlGetHash(window.location.href);
                this.elems[i].attr('href', href);
            }
            */
        }
        this.href = window.location.href;
    }
    this.timer = setTimeout(function() { liveUrl.update(); }, 500);
}

var liveUrl = new LiveUrl();

$(function () {
    $('.live-url').each(function() {
        liveUrl.add(this);
    });
});
