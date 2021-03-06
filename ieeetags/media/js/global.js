function getUrlParam(name, url) {
    if (typeof url == "undefined") {
        url = window.location.href;
    }
    var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(url);
    if (!results) {
        return 0;
    }
    return results[1] || 0;
}

function implode(glue, array) {
    var str = "";
    for (var i = 0; i < array.length; i++) {
        if (i)
            str += glue + array[i];
        else
            str += array[i];
    }
    return str;
}

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

    for (var argnum = 1; argnum < args.length; argnum++) {
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
        ( $.browser.msie && v >= 8 ) ||
        ( $.browser.firefox && v >= 3.6 ) ||
        ( $.browser.safari && v >= 4 ) ||
        ( $.browser.chrome && v >= 5 )
        );
}

function setBrowserCookie() {
    $('.browser-warning').remove();
    //set a cookie to show that the user has skipped the warning
    var options = { path: '/', expires: 1 };
    $.cookie("ignoreWarning", 'ignore', options);
}

$(function () {
    // get browser compatibility cookie
    var browser_cookie = $.cookie("ignoreWarning");

    // Show browser compatibility warning
    if (document.location.hostname.match(/^\m./) == null && browser_cookie != 'ignore' && !isCompatibleBrowser()) {
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
        $('label').each(function () {
            if ($(this).attr('for') == id)
                label = $(this);
        });
        if (label != null)
            this.options.highlightElem = label
    } else {
        this.options.highlightElem = $(this.options.highlightElem);
    }

    if (this.options.highlightElem == null) {
        ajax_report_error('HighlightCheckbox(): Error, this.options.highlightElem must be specified.');
        return;
    }

    this.elem.change(function (e) {
        highlightcheckbox.onChange(e);
    });

    this.elem.click(function (e) {
        highlightcheckbox.onChange(e);
    });

    this.onChange();
}

HighlightCheckbox.prototype.onChange = function (e) {
    if (this.elem.attr('checked')) {
        var classes = this.options.highlightElem.attr('className');
        var classes = classes ? classes.split(' ') : '';
        for (var i = 0; i < classes.length; i++) {
            if (classes[i].substr(classes[i].length - 10, 10) != '_highlight') {
                this.options.highlightElem.addClass(classes[i] + '_highlight');
            }
        }
    } else {
        var classes = this.options.highlightElem.attr('className').split(' ');
        for (var i = 0; i < classes.length; i++) {
            if (classes[i].substr(classes[i].length - 10) == '_highlight') {
                this.options.highlightElem.removeClass(classes[i]);
            }
        }
    }
};

function attachHighlightCheckboxes(elem) {
    if (elem) {
        elem.find('.highlight-checkbox').each(function () {
            new HighlightCheckbox(this);
        });
    } else {
        $('.highlight-checkbox').each(function () {
            new HighlightCheckbox(this);
        });
    }
}

//

function attachSelectCheckboxOnClick(elem) {
    elem = $(elem);
    elem.find('.select-checkbox-on-click').click(function () {
        $(this).find('input[type="checkbox"]').click();
        $(this).find('input[type="checkbox"]').change();
    });
    elem.find('.select-checkbox-on-click input[type="checkbox"]').click(function (e) {
        // Stop propagation to above function, otherwise checkbox is clicked twice & doesn't change
        e.stopPropagation();
    });
}

function attachItemsPerPage(elem) {
    if (elem == undefined) {
        elem = $('body');
    }

    elem.find('select.items-per-page').change(function () {
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
        for (var i = 0; i < this.form.elements.length; i++) {
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

        var fullurl = url + querystring + hash;

        window.location = fullurl;
    });
}

function attachSocietyLogoFlyovers(elem) {
    elem.find('img.logo-flyover').each(function () {
        Flyover.attach(this, {
            content_html: "<img src=\"" + $(this).metadata().full_url + "\" />"
        });
    });
}

function attachOtherConferencesToggle(elem) {
    elem.find('a.show-other-conferences, a.hide-other-conferences').each(function () {
        $(this).click(function () {
            $('#other-conferences-' + $(this).metadata().id).toggle();
            $('#show-other-conferences-' + $(this).metadata().id).toggle();
            $('#hide-other-conferences-' + $(this).metadata().id).toggle();
            return false;
        });
    });
}

function attachExpandSeries(elem) {
    elem.find('tr.current-conference').each(function () {
        var expandSeries = new ExpandSeries(this);
    });
}

function attachCopyTags(elem) {
    // Attach handlers to the "copy tags" links
    elem.find('a.copy-tags-to-clipboard').click(function () {
        var resourceId = $(this).metadata().resourceId;
        var linkElem = this;
        $.ajax({
            url: INDEX_URL + 'admin/ajax/copy_resource_tags',
            data: {
                resource_id: resourceId,
                csrfmiddlewaretoken: $('input:hidden[name="csrfmiddlewaretoken"]').val()
            },
            type: 'POST',
            success: function (data) {
                onCopyTagsSuccess(linkElem, data);
            }
        });

        return false;
    });

    // Attach handlers to the "paste tags" links
    elem.find('a.paste-tags').click(function () {
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
    $('.oldui .resources-lightbox-content').css('height', windowHeight - 220); // Blue container
    //$('#resource-tabs .nootabs-selected-tab').css('height', windowHeight - 320); // White container
    $('.oldui .nootabs-selected-tab div.group').css('height', windowHeight - 310);
    $('.oldui #xplore-results-container div.group').css('height', windowHeight - 362);
    $('.oldui #job-results-container div.group').css('height', windowHeight - 362);
    $('.oldui #education-results-container div.group').css('height', windowHeight - 310);
    $('.oldui #patents-tab div.group').css('height', windowHeight - 320);
}

function addCommas(nStr) {
    // From http://www.mredkj.com/javascript/nfbasic.html, public domain
    if (nStr == 'N/A') {
        return nStr;
    }
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

function getScrollBottom(elem) {
    return elem.prop("scrollHeight") - elem.scrollTop() - elem.outerHeight();
}

////////////////////////////////////////////////////////////////////////////////

var XPLORE_SORT_AUTHOR = 'au';
var XPLORE_SORT_TITLE = 'ti';
var XPLORE_SORT_AUTHOR_AFFILIATIONS = 'cs';
var XPLORE_SORT_PUBLICATION_TITLE = 'jn';
//var XPLORE_SORT_ARTICLE_NUMBER = 'an';
var XPLORE_SORT_PUBLICATION_YEAR = 'py';

var loadingTabs = [];
function removeNumRelatedLoader() {
    loadingTabs.pop();
    if (loadingTabs.length == 0) {
        $("#num-related-items-loading").remove();
    }
}

function getXploreSortName(sort) {
    if (sort == XPLORE_SORT_AUTHOR) {
        return 'Author';
    } else if (sort == XPLORE_SORT_TITLE) {
        return 'Title';
    } else if (sort == XPLORE_SORT_AUTHOR_AFFILIATIONS) {
        return 'Affiliations';
    } else if (sort == XPLORE_SORT_PUBLICATION_TITLE) {
        return 'Publication Title';
        //} else if (sort == XPLORE_SORT_ARTICLE_NUMBER) {
        //    return 'Article Number';
    } else if (sort == XPLORE_SORT_PUBLICATION_YEAR) {
        return 'Publication Year';
    }
    ajax_report_error('getXploreSortName(): ERROR: Unknown sort "' + sort + '"');
}

// This loads the resource results for a tag into the given element via AJAX.
function ResourceLoader(elem, ctype, showAll, sort) {
    console.log('ResourceLoader()');
    var resourceloader = this;
    this.elem = $(elem);
    this.listElem = this.elem.find('ul');
    this.scrollElem = this.elem.find('.group');
    this.loadingElem = null;
    this.isLoading = false;
    this.noResultsElem = null;
    this.ajaxToken = null;
    this.numResults = 0;
    this.totalsCalced = false;
    this.resultsGathered = false;
    this.data = null;

    this.scrollElem.scroll(function () {
        resourceloader.onScroll();
    });

    if (showAll == undefined) {
        showAll = false;
    }

    if (sort == undefined) {
        sort = null;
    }

    if (ctype == undefined) {
        ctype = null;
    }

    this.offset = 0;

    this.numXploreResultsPerPage = 10;

    this.tagId = this.elem.metadata().tagId;
    this.termId = this.elem.metadata().termId;

    this.showAll = showAll;
    this.sort = sort;
    this.sortDesc = false;
    this.ctype = ctype;

    $('#xplore-sort').click(function () {
        resourceloader.onChangeSelect();
    });
    $('#xplore-sort').change(function () {
        resourceloader.onChangeSelect();
    });

    this.loadContent();
}

ResourceLoader.prototype.onChangeSelect = function () {
    var sort = $('#xplore-sort').val();
    if (sort == '') {
        sort = null;
    }
    var desc = false;
    if (sort != null && sort[0] == '-') {
        log('setting desc');
        desc = true;
        sort = sort.substr(1, sort.length);
    }
    this.setSort(sort, desc);
};

ResourceLoader.prototype.setSort = function (sort, desc) {
    if (sort != this.sort || this.sortDesc != desc) {
        this.sort = sort;
        this.sortDesc = desc;
        // Clear the previous results.
        this.listElem.empty();
        // Reset to item #1.
        this.offset = 0;
        // Force another load to happen, regardless of if one is already happening.
        this.loadContent(true);
    }
};

ResourceLoader.prototype.loadContent = function (force) {
    console.log('ResourceLoader.loadContent()');
    loadingTabs.push(this.ctype);
    if (!this.isLoading || force) {
        this.isLoading = true;

        var resourceloader = this;
        this.ajaxToken = (new Date()).getTime() + '-' + Math.random();

        if (this.ctype == 'xplore') {
            this.url = '/ajax/xplore_results';
            this.data = {
                tag_id: this.tagId,
                term_id: this.termId,
                show_all: this.showAll,
                offset: this.offset,
                sort: this.sort,
                sort_desc: this.sortDesc,
                token: this.ajaxToken,
                ctype: null
            };
        } else if (this.ctype == 'education') {
            this.url = '/ajax/xplore_results';
            this.data = {
                tag_id: this.tagId,
                term_id: this.termId,
                show_all: this.showAll,
                offset: this.offset,
                sort: this.sort,
                sort_desc: this.sortDesc,
                token: this.ajaxToken,
                ctype: 'Educational Courses'
            };
        } else if (this.ctype == 'jobs') {
            this.url = '/ajax/jobs_results';
            this.data = {
                tag_id: this.tagId,
                term_id: this.termId,
                show_all: this.showAll,
                offset: this.offset,
                token: this.ajaxToken
            };
        } else if (this.ctype == 'tv') {
            this.url = '/ajax/tv_results';
            this.data = {
                tag_id: this.tagId,
                term_id: this.termId,
                show_all: this.showAll,
                offset: this.offset,
                token: this.ajaxToken
            };
        } else if (this.ctype == 'authors') {
            this.url = '/ajax/authors_results';
            this.data = {
                tag_id: this.tagId,
                term_id: this.termId,
                token: this.ajaxToken
            };
        }

        this.loadingElem = $('<div id="xplore-loading" class="loading">Loading ...<div></div></div>').appendTo(this.scrollElem);

        $("#xplore-loading div").spin({
            lines: 9, // The number of lines to draw
            length: 10, // The length of each line
            width: 8, // The line thickness
            radius: 15, // The radius of the inner circle
            corners: 1.0, // Corner roundness (0..1)
            speed: 2.2, // Rounds per second
            trail: 25 // Afterglow percentage
        });

        var url = this.url;
        console.log('url: ' + this.url);
        $.ajax({
            url: this.url,
            data: this.data,
            type: 'post',
            dataType: 'json',
            success: function (data) {
                console.log(url + ' -> ajax call success');
                resourceloader.onLoadData(data);
                var $favorite_stars = $('.favorite-job, .favorite-author, .favorite-article, .favorite-video');
                $favorite_stars.off('click').on('click', function(){
                    var action;
                    var externalId = $(this).data('nodeid');
                    var externalResourceType = $(this).data('rtype');
                    var title = $(this).prev().text();
                    if ($(this).hasClass('enabled')) {
                        action = 'disable';
                        $(this).removeClass('icon-star-whole enabled').addClass('icon-star');
                    } else {
                        action = 'enable';
                        $(this).removeClass('icon-star').addClass('icon-star-whole enabled');
                    }
                    $.post('/ajax/favorite-external/request',
                        {
                            action: action,
                            externalResourceType: externalResourceType,
                            externalId: externalId,
                            title: title
                        },
                        function () {
                            return false;
                        }
                    );
                });
            }
        });

        this.offset += this.numXploreResultsPerPage;
    }
};

ResourceLoader.prototype.onLoadData = function (data) {
    console.log('ResourceLoader.onLoadData');
    console.log(data);
    removeNumRelatedLoader();
    if (data.token == this.ajaxToken) {
        this.loadingElem.remove();
        this.loadingElem = null;
        if (data.num_results == parseInt(data.num_results)) {
            this.numResults += data.num_results;
        }

        if (data.num_results == 0 && this.numResults != 0) {
            this.resultsGathered = true;
        }

        if (this.noResultsElem) {
            this.noResultsElem.remove();
            this.noResultsElem = null;
        }

        if (data.xplore_error != null && data.num_results != 0) {
            // Xplore error, show the error message.
            this.errorElem = $('<p class="error"></p>').appendTo(this.scrollElem);
            this.errorElem.text(data.xplore_error);

        } else {
            // Normal results, load into the page.

            if (this.ctype == 'tv' || this.ctype == 'jobs') {
                this.scrollElem.append(data.html);
            } else {
                this.listElem[0].innerHTML += data.html;
            }

            resizeLightboxTab();

            // Hook up auto-truncate for the descriptions.
            autoTruncate(this.listElem.find('.auto-truncate-words'), { word_boundary: true });

            if (this.ctype == "education") {
                $('option#jump-to-articles').append('&nbsp;(' + addCommas(data.num_results) + ')');
                if (this.numResults != 0 && data.num_results != 0 || data.num_results == 'N/A') {
                    $('#num-education-results').text(addCommas(data.num_results));
                    var currentEdCount = parseInt($('#num-education-total-results').metadata().number);
                    var newEdCount = currentEdCount;
                    if (data.num_results == parseInt(data.num_results)) {
                        newEdCount += data.num_results;
                    }
                    $('#num-education-total-results').metadata().number = newEdCount;
                    $('#num-education-total-results').text(addCommas(newEdCount));
                }

            } else if (this.ctype == 'tv') {
                $('#num-tv-results').text(addCommas(data.num_results));
                $('option#jump-to-videos').append('&nbsp;(' + addCommas(data.num_results) + ')');
                var currentEdCount = parseInt($('#num-education-total-results').metadata().number);
                var newEdCount = currentEdCount;
                if (data.num_results == parseInt(data.num_results)) {
                    newEdCount += data.num_results;
                }
                $('#num-education-total-results').metadata().number = newEdCount;
                $('#num-education-total-results').text(addCommas(newEdCount));
                $('.favorite-video').qtip();
            } else if (this.ctype == 'jobs') {
                $('#num-job-results').text(addCommas(data.num_results));

                $('#job-url-container').html('<a href="' + data.job_url + '" target="_blank">View jobs on the IEEE Job Site <span class="popup newWindIcon"></span></a>');

                $('.favorite-job').qtip();
                if (data.num_results == 0) {
                    this.noResultsElem = $('<p class="no-resources">No Jobs are currently tagged "' + htmlentities(data.search_term) + '"</p>').appendTo(this.scrollElem);
                }
            } else {
                if (this.numResults != 0 && data.num_results != 0 || data.num_results == 'N/A') {
                    $('#num-' + this.ctype + '-results').text(addCommas(data.num_results));
                }
            }

            if (!this.totalsCalced) {
                var numRelatedItems = parseInt($('#num-related-items').metadata().number);
                var newTotal = numRelatedItems;
                if (data.num_results == parseInt(data.num_results)) {
                    newTotal += parseInt(data.num_results);
                }
                $('#num-related-items').text(addCommas(newTotal));
                $('#num-related-items').metadata().number = newTotal;
                this.totalsCalced = true;
            }

            if (data.num_results == 0 && this.numResults == 0) {
                if (this.ctype == "education") {
                    $('#num-education-results').text('0').parent('h3').addClass('no-education-results');
                    //$('#education-results-container .print-resource').remove();
                    //this.listElem.html('<p class="no-resources">No educational resources are currently tagged ' + $('#tag-name').text() + '</p>');
                } else if (this.ctype == 'tv') {
                    $('#num-tv-results').parent('h3').addClass('no-education-results');
                } else {
                    if (data.xplore_error) {
                        $('#num-' + this.ctype + '-results').text('N/A');
                        this.noResultsElem = $('<p class="no-resources">' + 'Xplore is not currently responding. Please try again later.'  + '</p>').appendTo(this.scrollElem);
                    } else if (!this.ctype == 'xplore') {
                        $('#num-' + this.ctype + '-results').text('0');
                        //$('#xplore-results-container .print-resource').remove();
                        this.noResultsElem = $('<p class="no-resources">No ' + this.ctype + ' Articles are currently tagged "' + htmlentities(data.search_term) + '"</p>').appendTo(this.scrollElem);
                    }
                }

            } else {
                var html = '<div class="articles-search">Show articles containing: <input class="live-search" id="article-live-search"><span id="article-search-clear" class="live-search-clear">&nbsp;</span></div>';
                html = ''; // removing search-in-xplore UI
                html += '<div class="articles-show-count">' + addCommas(data.num_results) + ' articles';
                if (!this.ctype) {
                    html += ' (<a href="http://xploreuat.ieee.org/search/freesearchresult.jsp?newsearch=true&queryText=' + escape(data.search_term) + '&x=0&y=0' + (this.ctype ? '&ctype=' + this.ctype : '') + '" target="_blank" rel="nofollow"><span>show search in Xplore</span><span class="popup newWinIcon"></span></a>)</div>'
                }
            }

            // Showing {{ xplore_results|length }} of {{ totalfound|intcomma }} results 

        }

        this.isLoading = false;
    }
};

ResourceLoader.prototype.onScroll = function () {
    if (!this.showAll) {
        var minScrollBottom = 10;
        var scrollBottom = getScrollBottom(this.scrollElem);
        if (scrollBottom <= minScrollBottom && !this.resultsGathered) {
            this.loadContent();
        }
    }
};

function attachResourceResults(elem, ctype, showAll) {
    console.log('attachResourceResults("' + elem + '", "'+ ctype +'")');
    if (showAll == undefined) {
        showAll = null;
    }
    new ResourceLoader(elem, ctype, showAll, null);
}

////////////////////////////////////////////////////////////////////////////////

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

function openIEEEtv(URL) {
    newWindow = window.open(URL, "ieeeTV", "scrollbars=no,resizable=no,HEIGHT=624,WIDTH=982");
    newWindow.focus();
}

// Add a custom outerHTML function to all jQuery objects.
jQuery.fn.outerHTML = function () {
    return $('<div>').append(this.eq(0).clone()).html();
};

function createUUID() {
    // http://www.ietf.org/rfc/rfc4122.txt
    var s = [];
    var hexDigits = "0123456789ABCDEF";
    for (var i = 0; i < 32; i++) {
        s[i] = hexDigits.substr(Math.floor(Math.random() * 0x10), 1);
    }
    s[12] = "4";  // bits 12-15 of the time_hi_and_version field to 0010
    s[16] = hexDigits.substr((s[16] & 0x3) | 0x8, 1);  // bits 6-7 of the clock_seq_hi_and_reserved to 01

    var uuid = s.join("");
    return uuid;
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

function ajax_report_error(msg) {
    log('ajax_report_error()');
    log('  msg: ' + msg);
    var vars = {};
    for (var i in window) {
        if (typeof window[i] == 'function') {
            //vars[i] = '(function)';
        } else if (typeof window[i] == 'object') {
            vars[i] = '(object)';
        } else {
            vars[i] = '' + window[i];
        }
    }
    $.post(
        INDEX_URL + 'ajax/javascript_error_log',
        {
            message: msg,
            url: window.location.href,
            vars: url_encode(vars)
        }
    );

    if (DEBUG) {
        alert('ajax_report_error(): ' + msg);
    }
}

var mouseX = null;
var mouseY = null;

$(function () {
    log('global.js');

    // Use the old style of ajax param serialization
    $.ajaxSettings.traditional = true;

    $('.select-checkbox-on-click').click(function () {
        $(this).find('input[type="checkbox"]').click();
        $(this).find('input[type="checkbox"]').change();
    });
    $('.select-checkbox-on-click input[type="checkbox"]').click(function (e) {
        // Stop propagation to above function, otherwise checkbox is clicked twice & doesn't change
        e.stopPropagation();
    });

    attachHighlightCheckboxes();
    attachItemsPerPage();

    // Bind a callback to any AJAX error (to prevent silent fails).
    $('body').bind(
        'ajaxError',
        function (event, XMLHttpRequest, textStatus, errorThrown) {

            // Ignore explicit xhr aborts
            if (XMLHttpRequest.statusText == "abort") {
                return;
            }
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
            divElem.css('z-index', '99999');
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

    setTimeout(function () {
        attachExpandSeries($(document));
    }, 500);

    attachCopyTags($(document));

    // Keep track of the mouse's position
    $().mousemove(function (e) {
        mouseX = e.pageX;
        mouseY = e.pageY;
    });

});

function setupQtips(sel, position, content, classes, showEvents) {
    var defaultPosition = {
        my: 'bottom center',
        at: 'top center'
    };
    $.extend(defaultPosition, {"my": $(sel).data('my'), "at": $(sel).data('at')});

    var defaultContent = {
        text: $(sel).next().html()
    };
    if (typeof position == "undefined" || !position) {
        position = {};
    }
    if (typeof content == "undefined" || !content) {
        content = {};
    }
    if (typeof showEvents == "undefined" || showEvents == null) {
        showEvents = 'mouseenter';
    }
    var defaultClasses = {
        classes: ''
    };
    position = $.extend(defaultPosition, position);
    content = $.extend(defaultContent, content);
    classes = $.extend(defaultClasses, classes);
    $(sel).qtip({
        content: content,
        style: {
            tip: {
                corner: true,
                width: 15,
                height: 10
            }
            //},
            //classes: classes
        },
        position: position,
        show: {
            solo: true,
            event: showEvents
        },
        hide: {
            delay: 300,
            fixed: true
        },
        events: {
            show: function (event, api) {
                api.elements.target.one('click', function () {
                    api.set('hide.event', 'unfocus');
                });
            },
            hide: function (event, api) {
                api.set('hide.event', 'mouseleave');
                event: 'unfocus';
            }
        }
    });
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
        }
    }
});
