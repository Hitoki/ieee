// Scales down the effect of the zoom.
function scaleZoom(zoom, scale) {
    if (zoom >= 100) {
        return (zoom - 100) * scale + 100;
    } else {
        return zoom;
    }
}

var sortDropDown, printDropDown, societyDropDown;
$(document).ready(function () {
    // Functions for tag landing pages only.
    if ($("body").hasClass("tag_base")) {
        // Adjust content padding depending on height of frozen header on tag landing pages.
        // var frozenHeadAdj = $("#tag_frozen_header").height() - 15;
        // $("#tag_contents").css("padding-top", frozenHeadAdj);

        // Handles smooth scroll to top of page.
        $(".topLink").click(function () {
            $('html, body').animate({ scrollTop: 0 }, 'slow');
        });
    }

    //hide the "Standards Board"
    $('#society-list-item-49').hide();

    // When clicking the help link, if the help panel is not shown, show it and abort.
    // Otherwise follow the link as normal
    $('#right-help').click(function () {
        if ($('#tag-help-box').is(':hidden')) {
            $('#tag-help-box').show();
            return false;
        }
        return true;
    });
    $("#tags-live-search").focus();

    var tagGalaxyWidth = $('#tag-galaxy').width();
    $('#bottom_fade').css('width', tagGalaxyWidth);

    // NEWUI
    $(".startTour").click(function () {
        $.cookie('ShowTour', null);
        startTour();
    });

    if ($('#tags').length) {
        $('.btn.startTour').show();
    }

    sortDropDown = $('#sortSelect').imageDropdown({'selectList': $("ul#sortSelect_options"), 'initialIndex': 0});
    if (sortDropDown) {
        sortDropDown.bind('change', function () {
            Tags.updateSort();
        });
    }
    printDropDown = $('#printSelect').imageDropdown({'selectList': $("ul#printSelect_options"), 'initialIndex': 0});

    societyDropDown = $('#societySelect').imageDropdown({'selectList': $("ul#societySelect_options"), 'initialIndex': 0});
    if (societyDropDown) {
        societyDropDown.bind('change', function () {
            Tags.selectSociety(societyDropDown.val());
        });
    }
    $('.org-clear').live(
        'click',
        function () {
            societyDropDown.setSelectedIndex(0);
        }
    );

    //Removes hover state from selected text when other option is chosen in dropdowns
    $(".customSelectList li").click(function () {
        $(".selected").removeClass("selected-hover");
        $(".customSelectContainer").blur();
    });

    $("#link-video").hover(function () {
        $("#video-link").addClass("video-image-hover");
        $("#video-icon").addClass("help-icon-hover");
    }, function () {
        $("#video-link").removeClass("video-image-hover");
        $("#video-icon").removeClass("help-icon-hover");
    });

    $("#link-help").hover(function () {
        $("#help-link").addClass("video-image-hover");
        $("#help-icon").addClass("help-icon-hover");
    }, function () {
        $("#help-link").removeClass("video-image-hover");
        $("#help-icon").removeClass("help-icon-hover");
    });

    $('#printSelect').live('mouseover', function () {
        $(this).children("#resource-print-icon").addClass("resource-print-icon-hover");
    }).live('mouseout', function () {
        $(this).children("#resource-print-icon").removeClass("resource-print-icon-hover");
    });

    $('#textui-zoom-container').live('mouseover', function () {
        $(this).children("#textui-zoom-slider").addClass("ui-widget-content-hover");
    }).live('mouseout', function () {
        $(this).children("#textui-zoom-slider").removeClass("ui-widget-content-hover");
    });

    $('#textui-tags-search-submit').click(function () {
        Tags.updateResults();
    });

    var qAutoload = getUrlParam('autoload');
    var qTab = getUrlParam('tab');
    if (qAutoload) {
        setTimeout(function () {
            Tags.selectTag(qAutoload, qTab || null);
        }, 3000);
    }

    // Handle nootabs.
    if ($('#left-column-container').length > 0) {
        var tabs = new Nootab($('#left-column-container'), {
            onChangeTab: function (tabs) {
                // Select the first item in the list ("All")
                var tab = tabs.getCurrentTab();
                if (tab.tab[0].id == 'sectors-tab') {
                    Tags.selectSector('all');
                } else if (tab.tab[0].id == 'societies-tab') {
                    Tags.selectSociety('all');
                } else {
                    ajax_report_error('onChangeTab(): Error: unknown tab id "' + tab.tab[0].id + '"');
                }
            }
        });
    }

    // Modification of accordion script to allow multiple panels to be open for conferences
    $("#notaccordion").find("h3")
        .addClass("notaccordion-header")
        .prepend('<span class="notaccordion-icon notaccordion-icon-e"></span>')
        .click(function () {
            if ($(this).hasClass("notaccordion-header-active")) {
                $(this)
                    .toggleClass("notaccordion-header-active")
                    .find("> .notaccordion-icon").addClass("notaccordion-icon-e").removeClass("notaccordion-icon-s").end()
                    .nextAll('div').hide();
                return false;
            } else {
                $(this)
                    .toggleClass("notaccordion-header-active")
                    .find("> .notaccordion-icon").addClass("notaccordion-icon-s").removeClass("notaccordion-icon-e").end()
                    .nextAll('div').show();
                return false;
            }
        })
        .nextAll('div').addClass("notaccordion-content").hide();
});

function splitContent(content, len) {
    if (content.length <= len) {
        return [content, ''];
    }
    var splitStr = '<!--SPLIT-->';
    var index = content.lastIndexOf(splitStr, len);
    if (index == -1) {
        index = content.length;
    }
    return [
        content.substr(0, index + splitStr.length)
        , content.substr(index + splitStr.length)
    ]
}

var CONTENT_CHUNK_SIZE = 40000;

var Tags = {

    PAGE_SECTOR: 'sector',
    PAGE_SECTOR_CLUSTER: 'sector_cluster',
    PAGE_SOCIETY: 'society',
    PAGE_SOCIETY_CLUSTER: 'society_cluster',
    PAGE_HELP: 'help',

    // The current page (sector, cluster, society, help, search, etc)
    page: null,
    isSearching: false,

    // Stores the a unique token for each AJAX request, so that we can ignore overlapping requests.
    ajaxToken: null,

    sectorId: null,
    societyId: null,
    clusterId: null,
    nodeType: null,
    // This is used to store info about the current node.  Useful for cluster name, etc.
    node: null,
    helpScreenElem: null,
    tagSortOverlayElem: null,
    oldHash: null,
    oldZoom: null,

    // Stores the default/initial zoom CSS values.
    defaultVertMargin: undefined,
    defaultHorizMargin: undefined,
    defaultTextSize: undefined,
    defaultHeight: undefined,
    defaultPadding: undefined,

    // This holds any remainder of the nodes/content, after we've loaded the intiial portion.  Used for progressive loading.
    remainingContent: null,

    init: function () {
        var tags = this;

        this.setDefaultZoomValues();
        tags.onChangeHash(encodeURIComponent(window.location.hash));

        // Need to manually call this when page is loaded if hash is empty.
        if (window.location.hash == '' || window.location.hash == '#') {
            this.onChangeHash(window.location.hash);
        }

        $('#tags').scroll(function () {
            tags.onScroll();
        });

        var url = location.pathname.split("/");
        if (url.length > 2 && url[2] == "account") {
            if ($('#yourfavsLink').length) {
                $('#yourfavsLink').click();
            } else {
                $('#signinLink').click();
            }
        }

        this.updateChangedNode();
    },

    onChangeHash: function (hash) {
        //log('onChangeHash()');
        if (this.oldHash != hash) {
            //log('  hash: ' + hash);
            //log('  this.oldHash: ' + this.oldHash);

            // Matches "#/sector/123"
            var sector_matches = hash.match(/^\/sector\/(all|\d+)$/);

            // Matches "#/sector/123/cluster/123"
            var cluster_sector_matches = hash.match(/^\/sector\/(all|\d+)\/cluster\/(\d+)$/);

            // Matches "#/organization/123"
            var society_matches = hash.match(/^\/organization\/(all|\d+)$/);

            // Matches "#/ogranization/123/cluster/123"
            var cluster_society_matches = hash.match(/^\/organization\/(all|\d+)\/cluster\/(\d+)$/);

            if (hash == '') {
                // Home page
                Tags.selectSociety('all');

            } else if (sector_matches) {
                // Special case: when first loading the http://host/textui/ page, the hash will be changed to http://host/textui/#/sector/all.  This prevents the second/extraneous AJAX reload:
                if (hash == '/sector/all' && this.oldHash == null && this.sectorId == 'all') {
                    return;
                }

                // Sector
                var sectorId = sector_matches[1];
                if (sectorId !== "all") {
                    sectorId = parseInt(sectorId);
                }

                // Make sure we don't load the same URL twice in a row.
                if (this.page != this.PAGE_SECTOR || this.sectorId != sectorId) {
                    this.selectSector(sectorId, false);
                }

            } else if (cluster_sector_matches) {
                // Cluster within a Sector
                var sectorId = cluster_sector_matches[1];
                var clusterId = parseInt(cluster_sector_matches[2]);
                if (sectorId !== "all") {
                    sectorId = parseInt(sectorId);
                }
                this.selectCluster(clusterId, sectorId, null, false);

            } else if (society_matches) {
                //'  got a society match.');
                // Society
                var societyId = society_matches[1];
                if (societyId !== "all") {
                    societyId = parseInt(societyId);
                }
                this.selectSociety(societyId, false);

            } else if (cluster_society_matches) {
                // Cluster within a Society
                var societyId = cluster_society_matches[1];
                var clusterId = parseInt(cluster_society_matches[2]);
                if (societyId !== "all") {
                    societyId = parseInt(societyId);
                }
                this.selectCluster(clusterId, null, societyId, false);

            } else {
                // Catch all for bad hashes... especially "#tag-login-tab" leftover from login redirect...
                Tags.selectSociety('all');
            }

            this.oldHash = hash;
        }
    },

    // This should be called any time the selected node has changed
    updateChangedNode: function () {
        //this.updateDisabledFilters();
        this.updateHighlightedNode();
        this.updateSwitchLink();

        if (this.page == this.PAGE_SECTOR || this.page == this.PAGE_SECTOR_CLUSTER || this.page == this.PAGE_SOCIETY || this.page == this.PAGE_SOCIETY_CLUSTER) {
            // Enable the slider
            $('#textui-zoom-slider').slider('enable');

            // Enable sorting
            if (this.tagSortOverlayElem) {
                Flyover.detach(this.tagSortOverlayElem);
                this.tagSortOverlayElem.remove();
                this.tagSortOverlayElem = null;
            }
            sortDropDown.enable();

            Flyover.detach(sortDropDown);
        } else {

            if (this.page == this.PAGE_HELP) {
                // Enable/disable the slider
                if ($('#tags-live-search').val().length >= 3) {
                    $('#textui-zoom-slider').slider('enable');
                } else {
                    $('#textui-zoom-slider').slider('disable');
                }
            } else {
                $('#textui-zoom-slider').slider('disable');
            }

            // Disable sorting
            if (!this.tagSortOverlayElem) {
                this.tagSortOverlayElem = $('<div id="tag-sort-overlay"></div>').appendTo('body');
                this.tagSortOverlayElem.bgiframe();

                var pos = sortDropDown.position();
                this.tagSortOverlayElem.css('top', pos.top);
                this.tagSortOverlayElem.css('left', pos.left);
                this.tagSortOverlayElem.css('width', sortDropDown.prop('offsetWidth'));
                this.tagSortOverlayElem.css('height', sortDropDown.prop('offsetHeight'));

                Flyover.attach(this.tagSortOverlayElem, {
                    'content': 'Please start by selecting an Industry Sector or IEEE Society',
                    'position': 'bottom'
                });
            }
            sortDropDown.disable();
        }
    },

    /*
    updateDisabledFilters: function() {
        //log('updateDisabledFilters()');
        //log(' this.sectorId: ' + this.node);
        if (this.sectorId == null) {
            // No node selected, disable filters
            $('#views input').attr('disabled', 'disabled');
            Flyover.attach($('#views'), {
                'content': 'Please start by selecting an Industry Section or IEEE Society'
            });
        } else {
            // Node selected, enable filters
            $('#views input').attr('disabled', '');
            Flyover.detach($('#views'));
        }
    },
    */

    _showWaitScreen: function () {
        // Hide the counts while loading.
        $('#tag-counts').hide();

        // Hide the content lightbox if it's visible.
        Lightbox.hide();

        // Hide any flyvoers so they don't persist when the node is gone.
        Flyover.hide();

        // Update the switch interfaces link
        this.updateChangedNode();

        var tagWindow = $("#tags");
        // unbind scroll event to avoid tags appearing under the loading animation
        // it will get reboud once the load is complete
        tagWindow.unbind('scroll');
        tagWindow.empty();
        tagWindow.html(
                '<div id="loading" class="please-wait">'
                + '<h1>Please wait...</h1><div></div>'
                + '</div>'
        );
        $(".please-wait div").spin({
            lines: 9, // The number of lines to draw
            length: 10, // The length of each line
            width: 8, // The line thickness
            radius: 15, // The radius of the inner circle
            corners: 1.0, // Corner roundness (0..1)
            speed: 2.2, // Rounds per second
            trail: 25, // Afterglow percentage
            zIndex: 99999 //Z-index
        });
    },

    // This is like _showWaitScreen(), but it shows the "Please wait" on top of the tags instead of replacing them.  Used for zooming.
    // If specified, the "callback" function is fired after the wait screen is shown.
    _showWaitScreenOver: function (callback) {
        //log('_showWaitScreenOver()');

        // Hide the content lightbox if it's visible.
        Lightbox.hide();

        // Hide any flyvoers so they don't persist when the node is gone.
        Flyover.hide();

        // Update the switch interfaces link
        this.updateChangedNode();

        Lightbox.show(null, {
            content: '<div class="please-wait"><h1>Please wait...</h1><div></div></div>',
            useBackground: false,
            onShowCallback: function () {
                // NOTE: Use a small delay to make sure the loading screen shows before the browser gets busy.
                setTimeout(callback, 1000);
            },
            parentElement: $('#tags'),
            customClass: 'lightbox-waiting-over',
            closeOnClickOutside: false
        });
        $(".please-wait div").spin({
            lines: 9, // The number of lines to draw
            length: 10, // The length of each line
            width: 8, // The line thickness
            radius: 15, // The radius of the inner circle
            corners: 1.0, // Corner roundness (0..1)
            speed: 2.2, // Rounds per second
            trail: 25 // Afterglow percentage
        });
    },

    _hideWaitScreenOver: function () {
        //log('_hideWaitScreenOver()');
        Lightbox.hide();
    },

    selectSector: function (sectorId, setHash) {
        //log('selectSector()');
        //log('  sectorId: ' + sectorId);
        if (setHash == undefined) {
            setHash = true;
        }

        this.page = this.PAGE_SECTOR;

        this.sectorId = sectorId;
        this.clusterId = null;
        this.societyId = null;
        this.nodeType = 'sector';

        if (setHash) {
            //log('setting hash to "' + '/sector/' + this.sectorId + '"');
            window.location.hash = encodeURIComponent('/sector/' + this.sectorId);
        }

        //log('selectSector(): calling updateResults().');
        this.updateResults();
    },

    selectSociety: function (societyId, setHash, reset) {
        //log('selectSociety()');
        //log('  societyId: ' + societyId);
        //log('  setHash: ' + setHash);
        if (this.page != this.PAGE_SOCIETY || this.societyId != societyId) {
            this.page = this.PAGE_SOCIETY;
            this.societyId = societyId;
        }

        if (reset) {
            this.sectorId = null;
            this.clusterId = null;
            this.nodeType = null;
        }

        if (setHash == undefined) {
            setHash = true;
        }

        if (setHash) {
            window.location.hash = encodeURIComponent('/organization/' + this.societyId);
            //log('setting hash to "' + '/oganization/' + this.societyId + '"');
        }
        //log('selectSociety(): calling updateResults().');        

        this.updateResults();

    },

    showSearchResults: function (search_for, showSearchResultsCallback) {
        this.isSearching = true;
        $('#tags-searching-msg').text('Filtering for "' + search_for + '"...').show();
        $('#tag-counts').hide();
        this.updateHighlightedNode();
        this._showWaitScreen();

        //log('showSearchResults(): calling updateResults().');
        this.updateResults(showSearchResultsCallback);
    },
    textuiNodes_xhr: null,
    updateResults: function (showSearchResultsCallback) {

        if (Tags.textuiNodes_xhr) {
            Tags.textuiNodes_xhr.abort();
        }
        this._showWaitScreen();
        //var filterStr = implode(',', this.getFilters());

        if ($('#tags-live-search').val().length >= 1) {
            $('#textui-tags-search-clear').css("display", "inline-block");
        } else {
            $('#textui-tags-search-clear').hide();
        }

        var search_for;

        if ($('#tags-live-search').val() == $('#tags-live-search').attr('placeholder')) {
            search_for = null;
        } else {
            search_for = $('#tags-live-search').val();
        }

        var showClusters;
        if ($('#show-clusters').length) {
            showClusters = $('#show-clusters').attr('checked');
        } else {
            // Default in case ENABLE_SHOW_CLUSTERS_CHECKBOX is false.
            showClusters = true;
        }

        var showTerms;
        if ($('#show-terms').length) {
            showTerms = $('#show-terms').attr('checked');
        } else {
            // Default in case ENABLE_SHOW_TERMS_CHECKBOX is false.
            showTerms = true;
        }

        if (this.sectorId != null) {
            // Load the sector/cluster
            //log('updateResults(): load sector/cluster');
            var token = createUUID();
            this.ajaxToken = token;
            Tags.textuiNodes_xhr = $.get(
                '/ajax/textui_nodes',
                {
                    sector_id: this.sectorId,
                    cluster_id: this.clusterId,
                    sort: this.getSort(),
                    search_for: search_for,
                    page: 'sector',
                    show_clusters: showClusters,
                    show_terms: showTerms,
                    token: token
                },
                function (data) {
                    Tags.onLoadResults(data);
                    if ($('#tag-counts').css('display') == 'none') {
                        $('#tag-counts').show();
                    }
                },
                'json'
            );
            this.updateHighlightedNode();

        } else if (this.societyId != null) {
            // Load the society
            //log('updateResults(): load society');
            var token = createUUID();
            this.ajaxToken = token;
            Tags.textuiNodes_xhr = $.get(
                '/ajax/textui_nodes',
                {
                    society_id: this.societyId,
                    cluster_id: this.clusterId,
                    sort: this.getSort(),
                    search_for: search_for,
                    page: 'society',
                    show_clusters: showClusters,
                    show_terms: showTerms,
                    token: token
                },
                function (data) {
                    Tags.onLoadResults(data);
                    if ($('#tag-counts').css('display') == 'none') {
                        $('#tag-counts').show();
                    }
                    if (showSearchResultsCallback) {
                        showSearchResultsCallback(search_for, data);
                    }
                },
                'json'
            );
            this.updateHighlightedNode();

        } else if (search_for != '') {
            // Search for tags in all societies/sectors.

            var page;
            if (this.page == PAGE_SECTOR || this.page == PAGE_SECTOR_CLUSTER) {
                page = 'sector';
            } else if (this.page == PAGE_SOCIETY || this.page == PAGE_SOCIETY_CLUSTER) {
                page = 'society';
            } else {
                ajax_report_error('Tags.updateResults(): ERROR: Unknown page ' + this.page);
                return;
            }

            //log('updateResults(): load search_for');
            var token = createUUID();
            this.ajaxToken = token;
            Tags.textuiNodes_xhr = $.get(
                '/ajax/textui_nodes',
                {
                    search_for: search_for,
                    society_id: this.societyId,
                    node_id: this.sectorId,
                    cluster_id: this.clusterId,
                    page: page,
                    show_clusters: showClusters,
                    show_terms: showTerms,
                    token: token
                },
                function (data) {
                    Tags.onLoadResults(data);
                    if (showSearchResultsCallback) {
                        showSearchResultsCallback(search_for, data);
                    }
                    if ($('#tag-counts').css('display') == 'none') {
                        $('#tag-counts').show();
                    }
                },
                'json'
            );

        } else {
            // Nothing selected
            Tags.selectSector('all');
        }
    },

    clearSearchResults: function () {
        //log('clearSearchResults()');
        $('#tag-counts').hide();
        $('#tags-live-search').val('');
        //log('clearSearchResults(): calling updateResults().');
        this.updateResults();
        tagsLiveSearch.lastValue = null;
    },

    onLoadResults: function (data) {
        // Only update the results if the token matches (ie. ignore all but the last AJAX request).
        if (data.token == this.ajaxToken) {

            var content = $('<div>').append(data.content);
            content.find('div').each(function () {
                var html;
                var args = "";
                var level = $(this).data('tag-level');
                var id = $(this).data('tag-id');
                var name = $(this).data('tag-name');
                var type = $(this).data('tag-type');
                var fly = "{ type: '" + type + "'}";
                $(this).addClass('node ' + type + ' flyover ' + fly);
                if (type == 'term') {
                    if ($(this).data('tag-score') == 1) {
                        $(this).addClass('node-taxonomy-term');
                    }
                    args = "_gaq.push(['_trackEvent', 'Terms', 'Click', '" + name + "']);";
                    html = '<a href="javascript:Tags.selectTag(' + id + ');" onClick="' + args + '" class=' + level + ' rel="nofollow"><span class="tag_icon tag-icon"></span> ' + name + '</a>';
                } else if (type == 'tag') {
                    args = "_gaq.push(['_trackEvent', 'Tags', 'Click', '" + name + "']);";
                    html = '<a href="javascript:Tags.selectTag(' + id + ');" onClick="' + args + '" class=' + level + ' rel="nofollow"><span class="tag_icon tag-icon"></span> ' + name + '</a>';
                } else if (type == 'tag_cluster') {
                    args = "_gaq.push(['_trackEvent', 'Cluster', 'Click', '" + args + "']);";
                    html = '<a href="javascript:$(\'#tags-live-search\').val(\'\'); Tags.selectCluster(' + $(this).data('cluster-args') + ');" onClick="' + args + '" class=' + level + ' rel="nofollow"><span class="icon_cluster_sm cluster-icon"></span> ' + name + '</a>';
                }
                if (html !== undefined) {
                    $(this).prepend(html);
                }
            });

            var content = $('<div>').append(content.clone()).html();

            this.remainingContent = content;
            this.textui_flyovers_url = data.textui_flyovers_url;
            $('#tag-counts').html(data.node_count_content);

            $('#tags').empty();
            this.loadContentChunk();

            // Rebind the scroll event
            var tags = this;
            $('#tags').scroll(function () {
                tags.onScroll();
            });
        }
    },

    updateHighlightedNode: function () {
        //log('updateHighlightedNode()');
        //log('  this.page: ' + this.page);
        //log('  this.clusterId: ' + this.clusterId);
        //log('  this.sectorId: ' + this.sectorId);

        // Remove any active sectors
        $('#sectors a.active-sector').removeClass('active-sector');
        $('#societies a.active-society').removeClass('active-society');
        $('#cluster').remove();

        $('#societySelect span span').html($('li#society-list-item-' + this.societyId + ' a').html());

        if (this.page == this.PAGE_SECTOR) {
            // Highlight the selected sector
            $('#sector-list-item-' + this.sectorId + ' a').addClass('active-sector');
            var tabs = $('#left-column-container').data('nootabs');
            tabs.setTab('sectors-tab');
            $('#tag-galaxy').addClass('tag-galaxy-viewing');

        } else if (this.page == this.PAGE_SECTOR_CLUSTER) {

            // Highlight the selected sector
            $('#sector-list-item-' + this.sectorId + ' a').addClass('active-sector');
            var tabs = $('#left-column-container').data('nootabs');
            tabs.setTab('sectors-tab');
            $('#tag-galaxy').addClass('tag-galaxy-viewing');

            // Highlight the selected cluster.
            // Create the cluster nav element.
            //log('  creating cluster nav element.');

            if (this.node && this.node.id == this.clusterId) {
                clusterName = this.node.name;
            } else {
                clusterName = '...';
            }

            function repr(val) {
                if (typeof(val) == 'string') {
                    val = val.replace('"', '\\"');
                    return '"' + val + '"';
                } else {
                    return val;
                }
            }

            // This formats the clusterId/sectorId values (since they can be "all" strings or numeric ID's)
            function temp_format_value(val) {
                if (val === null) {
                    return val;
                } else {
                    return htmlentities(repr(val));
                }
            }

            var elem = $('<li id="cluster"><a href="javascript:Tags.selectCluster(' + temp_format_value(this.clusterId) + ', ' + temp_format_value(this.sectorId) + ', null);" rel="nofollow">' + clusterName + '</a></li>');
            //log('<li id="cluster"><a href="javascript:Tags.selectCluster(' + temp_format_value(this.clusterId) + ', ' + temp_format_value(this.sectorId) + ', null);">' + clusterName + '</a></li>');

            if (this.sectorId) {
                $('#sector-list-item-' + this.sectorId).append(elem);
            } else {
                $('#sector-list-item-all').append(elem);
            }

            if (!this.node || this.node.id != this.clusterId) {
                // Repeat this function until the node info is loaded, so we can show the cluster name.
                setTimeout(
                    function () {
                        Tags.updateHighlightedNode();
                    },
                    300
                );
            }

        } else if (this.page == this.PAGE_SOCIETY_CLUSTER) {

            //log('  this.clusterId: ' + this.clusterId);

            // Highlight the selected society
            $('#society-list-item-' + this.societyId + ' a').addClass('active-society');
            var tabs = $('#left-column-container').data('nootabs');
            tabs.setTab('societies-tab');
            $('#tag-galaxy').addClass('tag-galaxy-viewing');

            // Highlight the selected cluster.
            // Create the cluster nav element.
            //log('  creating cluster nav element.');

            if (this.node && this.node.id == this.clusterId) {
                clusterName = this.node.name;
            } else {
                clusterName = '...';
            }

            function repr(val) {
                if (typeof(val) == 'string') {
                    val = val.replace('"', '\\"');
                    return '"' + val + '"';
                } else {
                    return val;
                }
            }

            // This formats the clusterId/societyId values (since they can be "all" strings or numeric ID's)
            function temp_format_value(val) {
                if (val === null) {
                    return val;
                } else {
                    return htmlentities(repr(val));
                }
            }

            var elem = $('<li id="cluster"><a href="javascript:Tags.selectCluster(' + temp_format_value(this.clusterId) + ', null, ' + temp_format_value(this.societyId) + ');" rel="nofollow">' + clusterName + '</a></li>');
            //log('<li id="cluster"><a href="javascript:Tags.selectCluster(' + temp_format_value(this.clusterId) + ', null, ' + temp_format_value(this.societyId) + ');">' + clusterName + '</a></li>');

            if (this.societyId) {
                $('#society-list-item-' + this.societyId).append(elem);
            } else {
                $('#society-list-item-all').append(elem);
            }

            if (!this.node || this.node.id != this.clusterId) {
                // Repeat this function until the node info is loaded, so we can show the cluster name.
                setTimeout(
                    function () {
                        Tags.updateHighlightedNode();
                    },
                    300
                );
            }

        } else if (this.page == this.PAGE_SOCIETY) {
            // Highlight the selected society
            $('#society-list-item-' + this.societyId + ' a').addClass('active-society');
            var tabs = $('#left-column-container').data('nootabs');
            tabs.setTab('societies-tab');
            $('#societies-tab').scrollTo($('#society-list-item-' + this.societyId), {offset: {top: -6, left: 0}});
            $('#tag-galaxy').addClass('tag-galaxy-viewing');
        } else {
            // No node selected
        }
    },

    selectCluster: function (clusterId, sectorId, societyId, setHash) {
        var tags = this;

        // unbind scroll event to avoid tags appearing under the loading animation
        // it will get reboud once the load is complete
        $('#tags').unbind('scroll');

        log("selectCluster()");
        log("  clusterId: " + clusterId);
        log("  sectorId: " + sectorId);
        log("  societyId: " + societyId);
        log("  setHash: " + setHash);

        if (setHash == undefined) {
            setHash = true;
        }

        if (sectorId != null && societyId != null) {
            ajax_report_error('Tags.selectCluster(): ERROR: Cannot specify both sectorId and societyId.');
            return;
        }

        var search_for;

        if ($('#tags-live-search').val() == $('#tags-live-search').attr('placeholder')) {
            search_for = null;
        } else {
            search_for = $('#tags-live-search').val();
        }

        var page;
        if (sectorId != null) {
            this.page = this.PAGE_SECTOR_CLUSTER;
            this.sectorId = sectorId;
            this.societyId = null;
            page = 'sector';
        } else if (societyId != null) {
            this.page = this.PAGE_SOCIETY_CLUSTER;
            this.societyId = societyId;
            this.sectorId = null;
            page = 'society';
        } else if (this.page == this.PAGE_SECTOR) {
            this.page = this.PAGE_SECTOR_CLUSTER;
            page = 'sector';
        } else if (this.page == this.PAGE_SOCIETY) {
            this.page = this.PAGE_SOCIETY_CLUSTER;
            page = 'society';
        } else {
            ajax_report_error('Error: Tags.selectCluster(), sectorId and societyId are not specified.');
            return;
        }

        this.clusterId = clusterId;

        this.node = null;
        this.nodeType = 'tag_cluster';
        this.updateChangedNode();

        var tagWindow = $("#tags");
        tagWindow.empty();
        tagWindow.html("<div class=\"empty-loading\"><h1 id=\"wait\">Please wait...</h1><div></div></div>");

        $(".empty-loading div").spin({
            lines: 9, // The number of lines to draw
            length: 10, // The length of each line
            width: 8, // The line thickness
            radius: 15, // The radius of the inner circle
            corners: 1.0, // Corner roundness (0..1)
            speed: 2.2, // Rounds per second
            trail: 25 // Afterglow percentage
        });

        var filterStr = implode(',', this.getFilters());

        // Hide any flyvoers so they don't persist when the node is gone.
        Flyover.hide();

        var showClusters;
        if ($('#show-clusters').length) {
            showClusters = $('#show-clusters').attr('checked');
        } else {
            // Default in case ENABLE_SHOW_CLUSTERS_CHECKBOX is false.
            showClusters = true;
        }

        var showTerms;
        if ($('#show-terms').length) {
            showTerms = $('#show-terms').attr('checked');
        } else {
            // Default in case ENABLE_SHOW_TERMS_CHECKBOX is false.
            showTerms = true;
        }

        log('selectCluster(): load cluster');
        var token = createUUID();
        this.ajaxToken = token;
        $.get(
            '/ajax/textui_nodes',
            {
                cluster_id: clusterId,
                sector_id: sectorId,
                society_id: societyId,
                filterValues: filterStr,
                sort: this.getSort(),
                page: page,
                show_clusters: showClusters,
                show_terms: showTerms,
                search_for: search_for,
                token: token
            },
            function (data) {
                Tags.onLoadResults(data);
            },
            'json'
        );

        // Get the cluster node's info (to display the name).
        log('Loading node info');
        $.getJSON(
            '/ajax/node',
            {
                nodeId: clusterId
            },
            function (data) {
                //log('Got node info');
                //log('  tags.clusterId: ' + tags.clusterId);
                //log('  data.id: ' + data.id);
                if (data.id == tags.clusterId) {
                    //log('node id matches.');
                    tags.node = data;
                }
            }
        );

        if (setHash) {
            if (this.sectorId) {
                var hash = '/sector/' + this.sectorId + '/cluster/' + this.clusterId;
                log('setting hash to "' + hash + '"');
                window.location.hash = encodeURIComponent(hash);
            } else if (this.societyId) {
                var hash = '/organization/' + this.societyId + '/cluster/' + this.clusterId;
                log('setting hash to "' + hash + '"');
                window.location.hash = encodeURIComponent(hash);
            } else {
                // fail.
                log('Tags.selectCluster(): ERROR: Neither sectorId or societyId are set.');
            }
        }
    },

    getTagById: function (id) {
        for (var i = 0; i < this.tags.length; i++) {
            if (this.tags[i].id == id) {
                return this.tags[i];
            }
        }
        return null;
    },

    selectTag: function (id, tabName, tour) {
        //log('selectTag()');
        //log('  id: ' + id);
        //log('  tabName: ' + tabName);
        this.updateChangedNode();

        //$('.tag').removeClass('activeTag');

        // Highlight the current tag
        var tagBlock = $('#tag-' + id);
        //tagBlock.addClass('activeTag');
        // Hide the flyover so it doesn't overlap with the lightbox
        Flyover.hide();

        // Show resource results in a lightbox
        if (tabName == undefined) {
            initialTab = 'overview';
        } else {
            initialTab = tabName;
        }

        Lightbox.hide();
        Lightbox.show('/ajax/tag_content/' + id + '/textui/' + initialTab + '?load_framework=True', {
            verticalCenter: false,
            customClass: 'resources',
            onShowCallback: function () {
                if (tabName != undefined) {
                    // if there was no tab name given, use the default tab
                    log('  calling Tags.onSelectTag()');
                    Tags.onSelectTag(tabName);
                }
                if (tour != undefined) {
                    $('.resources-lightbox-content').append('<ol id="modal-tour" style="display:none;"><li>hi</li></ol>');
                }

                $("#xplore-overview-loading, #num-related-items-loading").spin({
                    lines: 9, // The number of lines to draw
                    length: 2, // The length of each line
                    width: 2, // The line thickness
                    radius: 3, // The radius of the inner circle
                    corners: 1.0, // Corner roundness (0..1)
                    speed: 2.2, // Rounds per second
                    trail: 25 // Afterglow percentage
                });

                // populate the patent tab.
                //patentSearch = new google.search.PatentSearch();
                //patentSearch.setResultSetSize(8);
                //patentSearch.setNoHtmlGeneration();

                // Set searchComplete as the callback function when a search is 
                // complete.  The patentSearch object will have results in it.
                //patentSearch.setSearchCompleteCallback(this,
                //   function(){
                //       if (typeof patentSearch.cursor != "undefined"){
                //       $.each(patentSearch.results, function(i, result){
                //           $('#patents-tab div.group').append($(result.html));
                //           $('#patents-tab a span').text(patentSearch.cursor.estimatedResultCount); // patentSearch.cursor.estimatedResultCount
                //       });
                //       var numRelatedItems = parseInt($('#num-related-items').metadata().number);
                //       var newTotal = numRelatedItems + parseInt(patentSearch.cursor.estimatedResultCount);
                //       $('#num-related-items').text(addCommas(newTotal));
                //       $('#num-related-items').metadata().number = newTotal;

                //       $("<span class='newWindowIcon'></span>").insertAfter("a.gs-title");
                //       if (patentSearch.cursor.estimatedResultCount > 8) {
                //           var moreResultsLink = $('<a target="_blank">More results on Google</a>');
                //           moreResultsLink.attr('href', patentSearch.cursor.moreResultsUrl);
                //           $('#patents-tab div.group').append(moreResultsLink);
                //       }
                //    }
                //   }
                //   , null);

                // Specify search quer(ies)
                //patentSearch.execute($('div.[id="tag-' + id + '"]:first').text());

                // Include the required Google branding
                //google.search.Search.getBranding('branding');

                $(document).trigger('onShowLightboxTab');
            },
            showCloseButton: true
        });
        $('.resources-lightbox-content').append($('<div class="resource-loading">'));
        $(".resource-loading").spin({
            lines: 9, // The number of lines to draw
            length: 10, // The length of each line
            width: 8, // The line thickness
            radius: 15, // The radius of the inner circle
            corners: 1.0, // Corner roundness (0..1)
            speed: 2.2, // Rounds per second
            trail: 25, // Afterglow percentage
            color: '#FFFFFF',
        });
    },

    onSelectTag: function (tabName) {
        var tabs = $('#resource-tabs').data('nootabs');
        tabs.setTab(tabName);
    },

    getFilters: function () {
        var result = [];
        var filters = $('.filter');
        for (var i = 0; i < filters.length; i++) {
            //console.log("i: " + i);
            //console.log("filters[i].id: " + filters[i].id);
            //console.log("filters[i].value: " + filters[i].value);
            //console.log("filters[i].checked: " + filters[i].checked);
            if (filters[i].checked)
                result.push(filters[i].value);
        }
        return result;
    },

    getSort: function () {
        return sortDropDown.val();
    },

    updateSwitchLink: function () {
        // NOTE: Roamer is disabled. No need for switch link.
        //if (this.sectorId != null) {
        //    if (this.nodeType == 'sector') {
        //        $('#switch-link').attr('href', '/roamer#/sector/' + this.sectorId);
        //    } else {
        //        ajax_report_error('ERROR in updateSwitchLink(): Unrecognized nodeType "' + this.nodeType + '"');
        //        return;
        //    }
        //} else {
        //    $('#switch-link').attr('href', '/roamer');
        //}
    },

    updateSort: function () {
        if (this.page == this.PAGE_SECTOR) {
            this.selectSector(this.sectorId);
        } else if (this.page == this.PAGE_SECTOR_CLUSTER) {
            this.selectCluster(this.clusterId, this.sectorId, null);
        } else if (this.page == this.PAGE_SOCIETY_CLUSTER) {
            this.selectCluster(this.clusterId, null, this.societyId);
        } else if (this.page == this.PAGE_SOCIETY) {
            this.selectSociety(this.societyId);
        } else {
            ajax_report_error('Tags.updateSort(): Error, page (' + this.page + ') must be "sector", "tag_cluster", or "society".');
        }
    },

    clearSectorSociety: function (setHash) {
        this.page = null;
        this.sectorId = null;
        this.clusterId = null;
        this.societyId = "all";
        $('#tags-live-search').val('');
        //log('clearSectorSociety(): calling updateResults().');
        this.updateResults();
        $('#tag-galaxy').removeClass('tag-galaxy-viewing');
        $("#tags-live-search").focus();
    },

    setDefaultZoomValues: function () {
        var tag = $('#default-height-tag');
        if (tag.length == 0) {
            ajax_report_error('ERROR: In setDefaultZoomValues(), could not find #default-height-tag element.');
            return;
        }

        var clusterIcon = tag.find('.cluster-icon');
        if (clusterIcon.length == 0) {
            ajax_report_error('ERROR: In setDefaultZoomValues(), could not find #default-height-tag .cluster-icon element.');
            return;
        }

        this.defaultVertMargin = Math.round(parseInt(tag.css('margin-top')));
        this.defaultHorizMargin = Math.round(parseInt(tag.css('margin-left')));
        this.defaultTextSize = Math.round(parseInt(tag.css('font-size')));

        // In IE, the CSS 'height' is 'auto'.
        var height = parseInt(tag.css('height'));
        if (isNaN(height)) {
            this.defaultHeight = tag.prop('offsetHeight');
        } else {
            this.defaultHeight = Math.round(height);
        }

        this.defaultPadding = Math.round(parseInt(tag.css('padding-top')));

        if (clusterIcon.length) {
            this.defaultClusterIconWidth = clusterIcon[0].offsetWidth;
            this.defaultClusterIconHeight = clusterIcon[0].offsetHeight;
        } else {
            this.defaultClusterIconWidth = null;
            this.defaultClusterIconHeight = null;
        }

        /*
         log('  this.defaultVertMargin: ' + this.defaultVertMargin);
         log('  this.defaultHorizMargin: ' + this.defaultHorizMargin);
         log('  this.defaultTextSize: ' + this.defaultTextSize);
         log('  this.defaultHeight: ' + this.defaultHeight);
         log('  this.defaultPadding: ' + this.defaultPadding);
         log('  this.defaultClusterIconWidth: ' + this.defaultClusterIconWidth);
         log('  this.defaultClusterIconHeight: ' + this.defaultClusterIconHeight);
         */
    },

    updateZoom: function (elem) {
        var tags = this;

        //log('updateZoom()');
        //log('  elem: ' + elem);
        if (elem == undefined) {
            // Search all nodes on the page.
            //log('Search all nodes on the page.');
            elem = $('#tags');
        } else {
            //log('  elem.length: ' + elem.length);
            //log('  elem[0]: ' + elem[0]);
        }
        //log('  Found ' + elem.find('.node').length + ' nodes.');

        var zoom = $('#textui-zoom-slider').slider('value');

        // Only zoom if necessary (either the zoom is not 100, or the zoom is 100 but wasn't before).
        if (zoom != 100 || (this.oldZoom != null && this.oldZoom != zoom)) {
            log('zooming to ' + zoom + '%');

            if (zoom != 100) {
                $('#textui-zoom-default-zoom').css('display', 'block');
            } else {
                $('#textui-zoom-default-zoom').css('display', 'none');
            }

            $('#textui-zoom-value').text(zoom + '%');

            this._showWaitScreenOver(function () {
                // This function is called after the waiting screen is shown.
                elem.find('.node').css('margin-top', (tags.defaultVertMargin * zoom / 100) + 'px');
                elem.find('.node').css('margin-bottom', (tags.defaultVertMargin * zoom / 100) + 'px');
                elem.find('.node').css('margin-left', (tags.defaultHorizMargin * zoom / 100) + 'px');
                elem.find('.node').css('margin-right', (tags.defaultHorizMargin * zoom / 100) + 'px');
                elem.find('.node').css('font-size', (tags.defaultTextSize * zoom / 100) + 'px');
                elem.find('.node').css('height', (tags.defaultHeight * zoom / 100) + 'px');
                elem.find('.node').css('padding-top', (tags.defaultPadding * scaleZoom(zoom, 2) / 100) + 'px');
                elem.find('.node').css('padding-bottom', (tags.defaultPadding * scaleZoom(zoom, 2) / 100) + 'px');
                elem.find('.node').css('padding-left', (tags.defaultPadding * scaleZoom(zoom, 3) / 100) + 'px');
                elem.find('.node').css('padding-right', (tags.defaultPadding * scaleZoom(zoom, 3) / 100) + 'px');

                //elem.find('.cluster-icon').css({
                //    width: (tags.defaultClusterIconWidth * scaleZoom(zoom, 1) / 100) + 'px'
                //    , height: (tags.defaultClusterIconHeight * scaleZoom(zoom, 1) / 100) + 'px'
                //});

                // Add another content chunk if the tag container is not full.
                if ($('#tags').prop("scrollHeight") <= $('#tags').outerHeight() + $('#tags-chunk-loading').outerHeight()) {
                    tags.loadContentChunk();
                }

                tags._hideWaitScreenOver();

                if (tags_callback) {
                    tags_callback();
                }
            });

        } else {
            if (tags_callback) {
                tags_callback();
            }
        }

        this.oldZoom = zoom;

        //log('~resizeNodes()');
    },

    onScroll: function () {
        var scrollBottom = getScrollBottom($('#tags'));
        var minScrollBottom = 10;
        if (scrollBottom <= minScrollBottom) {
            this.loadContentChunk();
        }
    },

    loadContentChunk: function () {
        //log('loadContentChunk()');

        // Hide the loading banner.
        $('#tags-chunk-loading').remove();

        var tagWindow = $("#tags");

        if (ENABLE_PROGRESSIVE_LOADING) {
            // Get the next chunk of contents.
            var results = splitContent(this.remainingContent, CONTENT_CHUNK_SIZE);
            var chunk = results[0];
            this.remainingContent = results[1];
        } else {
            // Load the entire contents at once.
            var chunk = this.remainingContent;
            this.remainingContent = '';
        }

        //log('  -chunk.length: ' + chunk.length);
        //log('  -this.remainingContent.length: ' + this.remainingContent.length);

        if (chunk.length > 0) {
            //log('  chunk: ' + chunk);
            //log('  this.remainingContent: ' + this.remainingContent);

            // Load the next chunk of content into the tags div.
            //tagWindow.html(tagWindow.html() + chunk);

            var zoom = $('#textui-zoom-slider').slider('value');

            if (zoom != 100) {

                // Add inline style="" to all DIV's, to prevent nodes from briefly showing up full-size.
                //log('adding STYLE attrs.');

                // Add zoom styles to nodes.
                var s = [];
                s.push('margin-top:' + (this.defaultVertMargin * zoom / 100) + 'px');
                s.push('margin-bottom:' + (this.defaultVertMargin * zoom / 100) + 'px');
                s.push('margin-left:' + (this.defaultHorizMargin * zoom / 100) + 'px');
                s.push('margin-right:' + (this.defaultHorizMargin * zoom / 100) + 'px');
                s.push('font-size:' + (this.defaultTextSize * zoom / 100) + 'px');
                s.push('height:' + (this.defaultHeight * zoom / 100) + 'px');
                s.push('padding-top:' + (this.defaultPadding * scaleZoom(zoom, 2) / 100) + 'px');
                s.push('padding-bottom:' + (this.defaultPadding * scaleZoom(zoom, 2) / 100) + 'px');
                s.push('padding-left:' + (this.defaultPadding * scaleZoom(zoom, 3) / 100) + 'px');
                s.push('padding-right:' + (this.defaultPadding * scaleZoom(zoom, 3) / 100) + 'px');
                s = s.join('; ');
                chunk = chunk.replace(/(<div [^>]+)(>)/gi, '$1 style="' + s + '" $2');

                // Add zoom styles to cluster icons.
                //var s = [];
                //s.push('width:' + (this.defaultClusterIconWidth * scaleZoom(zoom, 1) / 100) + 'px');
                //s.push('height:' + (this.defaultClusterIconHeight * scaleZoom(zoom, 1) / 100) + 'px');
                //s = s.join('; ');
                //chunk = chunk.replace(/(<img [^>]+ class="cluster-icon")\s*(\/>)/gi, '$1 style="' + s + '" $2')
            }

            // NOTE: This next line causes Firefox to give "script stack space quota is exhausted" error.  Using innerHTML fixes this.
            //var chunkElem = $('<span>' + chunk + '</span>');
            var chunkElem = $('<div></div>');
            chunkElem[0].innerHTML = chunk;

            //log('chunkElem: ');
            //console.log(chunkElem);
            //log('chunkElem.length: ' + chunkElem.length);

            tagWindow.append(chunkElem);
            // NOTE: This isn't any faster:
            //tagWindow[0].innerHTML += chunk;

            // Calling special function to avoid code bloat due to duplication. The string "tagid" in the url will be replaced with the
            // actual id.
            /*
             attachTextUiFlyovers(
                 '#tags',
                 {
                     url: this.textui_flyovers_url,
                     position: 'auto',
                     customClass: 'textui-node',
                     hideDelay: 400,
                     positionCursor: false,
                     closeButton: true,
                     useWaitCursor: true
                 }
             );
             */
            if (this.remainingContent.length > 0) {
                // Show the loading banner if there is still remaining content.
                tagWindow.append($(''
                        + '<div id="tags-chunk-loading">'
                            + '<p>Loading...</p><div></div>'
                        + '</div>'
                ));
                // Add another content chunk if we haven't filled the container yet.
                if ($('#tags').prop("scrollHeight") <= $('#tags').outerHeight() + $('#tags-chunk-loading').outerHeight()) {
                    this.loadContentChunk();
                }
            }
        }
    }
};
