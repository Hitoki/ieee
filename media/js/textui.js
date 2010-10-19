
function getNode(parent, name) {
    var nodes = parent.getElementsByTagName(name);
    if (nodes.length != 1) {
        alert("getNode(" + parent + ", " + name + "): found " + nodes.length + " nodes.");
        return null;
    }
    return nodes[0];
}

var sortDropDown, printDropDown;
$(document).ready(function(){
    if ($.cookie("noShowHelpBox")){
        $('#tag-help-box').hide();
    }
    
	// When clicking the help link, if the help panel is not shown, show it and abort.
	// Otherwise follow the link as normal
    $('#right-help').click(function(){
       if($('#tag-help-box').is(':hidden')){
           $('#tag-help-box').show();
           return false;
       }
       return true;
    });
    $("#tags-live-search").focus();
    
    function hideHelpBox() {
        var windowHeight = $(window).height();
        var navTabsHeight = $('#galaxy-tabs .nootabs-menu').eq(0).height();
        
        $('#tag-help-box').hide();
        $('div#sectors-tab, div#societies-tab').css('height', windowHeight - 343 - navTabsHeight);
        $('div#sectors-tab, div#societies-tab').css('min-height', 437 - navTabsHeight);
    }
    
    $('#help-close-button').click(function(){
        hideHelpBox();
    });
    
    $('#no-show-box').click(function(){
        //set a cookie to show that the user hidden the help box
        var options = { path: '/', expires: 7 };
        $.cookie("noShowHelpBox", 'true', options);
        
        hideHelpBox();
        
    });
    
    sortDropDown = $('#sortSelect').imageDropdown({'selectList': $("ul#sortSelect_options"), 'initialIndex': 0});
    sortDropDown.bind('change', function(){
        Tags.updateSort();
    });
    printDropDown = $('#printSelect').imageDropdown({'selectList': $("ul#printSelect_options"), 'initialIndex': 0});
    
    //Removes hover state from selected text when other option is chosen in dropdowns
    $(".customSelectList li").click(function() {
         $(".selected").removeClass("selected-hover");
         $(".customSelectContainer").blur();
    });
    
    $("#link-video").hover(function() {
        $("#video-link").addClass("video-image-hover");
        $("#video-icon").addClass("help-icon-hover");
    }, function() {
        $("#video-link").removeClass("video-image-hover");
        $("#video-icon").removeClass("help-icon-hover");
    });
    
    $("#link-help").hover(function() {
        $("#help-link").addClass("video-image-hover");
        $("#help-icon").addClass("help-icon-hover");
    }, function() {
        $("#help-link").removeClass("video-image-hover");
        $("#help-icon").removeClass("help-icon-hover");
    });
    
    $('#printSelect').live('mouseover',function(){
        $(this).children("#resource-print-icon").addClass("resource-print-icon-hover");
    }).live('mouseout', function(){
        $(this).children("#resource-print-icon").removeClass("resource-print-icon-hover");
    });
    
    $('#textui-zoom-container').live('mouseover',function(){
        $(this).children("#textui-zoom-slider").addClass("ui-widget-content-hover");
    }).live('mouseout', function(){
        $(this).children("#textui-zoom-slider").removeClass("ui-widget-content-hover");
    });
    
	var matches = window.location.search.match('autoload=([0-9]*)');
	if (matches){
        setTimeout(function(){Tags.selectTag(matches[1]);}, 3000);
    }
});

var Tags = {
    
    PAGE_SECTOR: 'sector',
    PAGE_SECTOR_CLUSTER: 'sector_cluster',
    PAGE_SOCIETY: 'society',
    PAGE_SOCIETY_CLUSTER: 'society_cluster',
    PAGE_HELP: 'help',
    
    // The current page (sector, cluster, society, help, search, etc)
    page: null,
    isSearching: false,
    
    sectorId: null,
    societyId: null,
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
    
    init: function() {
        var tags = this;
        
        $.historyInit(function(hash) {
            tags.onChangeHash(hash);
        });
        
        // Need to manually call this when page is loaded if hash is empty.
        if (window.location.hash == '' || window.location.hash == '#') {
            this.onChangeHash(window.location.hash);
        }
        
        this.updateChangedNode();
    },
    
    onChangeHash: function(hash) {
        //log('onChangeHash()');
        if (this.oldHash != hash) {
            //log('  hash: ' + hash);
            
            // Matches "#/sector/123"
            var sector_matches = hash.match(/^\/sector\/(all|\d+)$/);
            
            // Matches "#/society/123"
            var society_matches = hash.match(/^\/society\/(all|\d+)$/);
            
            if (hash == '') {
                // Home page
                Tags.selectSector('all');
                
            } else if (sector_matches) {
                // Sector
                var sectorId = sector_matches[1];
                if (sectorId !== "all") {
                    sectorId = parseInt(sectorId);
                }
                if (this.sectorId != sectorId) {
                    this.selectSector(sectorId, false);
                }
            
            } else if (society_matches) {
                // Society
                var societyId = society_matches[1];
                if (societyId !== "all"){
                    societyId = parseInt(societyId);
                }
                if (this.societyId != societyId) {
                    this.selectSociety(societyId, false);
                }
            
            } else {
                // Catch all for bad hashes... especially "#tag-login-tab" leftover from login redirect...
                Tags.selectSector('all');
                
            }
            
            this.oldHash = hash;
        }
    },
    
    // This should be called any time the selected node has changed
    updateChangedNode: function() {
        //this.updateDisabledFilters();
        this.updateHighlightedNode();
        this.updateSwitchLink();
        
        if (this.page == this.PAGE_SECTOR || this.page == this.PAGE_SECTOR_CLUSTER || this.page == this.PAGE_SOCIETY) {
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
                this.tagSortOverlayElem.css('width', sortDropDown.attr('offsetWidth'));
                this.tagSortOverlayElem.css('height', sortDropDown.attr('offsetHeight'));
                
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
    
    _showWaitScreen: function() {
        // Hide the content lightbox if it's visible.
        Lightbox.hide();
        
        // Hide any flyvoers so they don't persist when the node is gone.
        Flyover.hide();
        
        // Update the switch interfaces link
        this.updateChangedNode();
    
        var tagWindow = $("#tags");
        tagWindow.empty();
        tagWindow.html(
            '<div id="loading" class="please-wait">'
            + '<h1>Please wait...</h1>'
            + '<img src="' + MEDIA_URL + '/images/ajax-loader-bar.gif" />'
            + '</div>'
        );
        
    },
    
    // This is like _showWaitScreen(), but it shows the "Please wait" on top of the tags instead of replacing them.  Used for zooming.
    // If specified, the "callback" function is fired after the wait screen is shown.
    _showWaitScreenOver: function(callback) {
        log('_showWaitScreenOver()');
        
        // Hide the content lightbox if it's visible.
        Lightbox.hide();
        
        // Hide any flyvoers so they don't persist when the node is gone.
        Flyover.hide();
        
        // Update the switch interfaces link
        this.updateChangedNode();
        
        Lightbox.show(null, {
            content:
                '<h1>Please wait...</h1>'
                + '<img src="' + MEDIA_URL + '/images/ajax-loader-bar.gif" />'
            , useBackground: false
            , onShowCallback: function() {
                // NOTE: Use a small delay to make sure the loading screen shows before the browser gets busy.
                setTimeout(callback, 1000);
            }
            , parentElement: $('#tags')
            , customClass: 'lightbox-waiting-over'
            , closeOnClickOutside: false
        });
    },
    
    _hideWaitScreenOver: function() {
        log('_hideWaitScreenOver()');
        Lightbox.hide();
    },
    
    selectSector: function(sectorId, setHash) {
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
            $.historyLoad('/sector/' + this.sectorId);
        }
        
        this.updateResults();
    },
    
    selectSociety: function(societyId, setHash) {
        //log('selectSociety()');
        //log('  societyId: ' + societyId);
        
        this.page = this.PAGE_SOCIETY
        
        this.societyId = societyId;
        this.sectorId = null;
        this.clusterId = null;
        this.nodeType = null;
        
        if (setHash == undefined) {
            setHash = true;
        }
        
        if (setHash) {
            //log('setting hash to "' + '/sector/' + this.sectorId + '"');
            $.historyLoad('/society/' + this.societyId);
        }
        
        this.updateResults();
    },
    
    showSearchResults: function(search_for, showSearchResultsCallback) {
        log('showSearchResults()');
        
        this.isSearching = true;
        
        this.updateHighlightedNode();
        
        this._showWaitScreen();
        
        log('  searching for "' + search_for + '"');
        
        this.updateResults(showSearchResultsCallback);
        //var data = {
        //    search_for: search_for
        //};
        //if (this.page == this.PAGE_SOCIETY) {
        //    log('  was society, adding to data');
        //    data.society_id = this.societyId;
        //} else if (this.page == this.PAGE_SECTOR) {
        //    log('  was sector, adding to data');
        //    data.node_id = this.sectorId;
        //} else if (this.page == this.PAGE_HELP) {
        //    log('  was help, doing nothing');
        //    // Do nothing
        //} else {
        //    alert('Tags.showSearchResults(): Error, unknown page ' + this.page);
        //    return;
        //}
        //
        //$.ajax({
        //    url: '/ajax/textui_nodes',
        //    data: data,
        //    success: function(data) {
        //        Tags.onLoadResults(data);
        //        if (showSearchResultsCallback) {
        //            showSearchResultsCallback(search_for, data);
        //        }
        //    }
        //});
    },
	
    updateResults: function(showSearchResultsCallback) {
        this._showWaitScreen();
        //var filterStr = implode(',', this.getFilters());
        
            
        if ($('#tags-live-search').val().length >= 1) {
            $('#textui-tags-search-clear').show();
        } else {
            $('#textui-tags-search-clear').hide();
        }
        
        var search_for = $('#tags-live-search').val();
        
        if (this.sectorId != null) {
            // Load the sector/cluster
            $.ajax({
                url: '/ajax/textui_nodes',
                data: {
                    node_id: this.sectorId,
                    sort: this.getSort(),
                    search_for: search_for
                },
                success: function(data) {
                    Tags.onLoadResults(data);
                }
            });
            this.updateHighlightedNode();
            
        } else if (this.societyId != null) {
            // Load the society
            $.ajax({
                url: '/ajax/textui_nodes',
                data: {
                    society_id: this.societyId,
                    sort: this.getSort(),
                    search_for: search_for
                },
                success: function(data) {
                    Tags.onLoadResults(data);
                }
            });
            this.updateHighlightedNode();
        
        } else if (search_for != '') {
            // Search for tags
            
            var data = {
                search_for: search_for,
                society_id: this.societyId,
                node_id: this.sectorId
            };
            
            $.ajax({
                url: '/ajax/textui_nodes',
                data: data,
                success: function(data) {
                    Tags.onLoadResults(data);
                    if (showSearchResultsCallback) {
                        showSearchResultsCallback(search_for, data);
                    }
                }
            });            
            
        } else {
            // Nothing selected
            Tags.selectSector('all');
            
        }
        
    },
    
	clearSearchResults: function() {
        log('clearSearchResults()');
        $('#tags-live-search').val('');
        this.updateResults();
	},
    
    onLoadResults: function(data) {
        var tagWindow = $("#tags");
        tagWindow.html(data);
		this.updateZoom();
    },
    
    updateHighlightedNode: function() {
        log('updateHighlightedNode()');
        log('  this.page: ' + this.page);
        log('  this.clusterId: ' + this.clusterId);
        log('  this.sectorId: ' + this.sectorId);
        
        // Remove any active sectors
        $('#sectors a.active-sector').removeClass('active-sector');
        $('#societies a.active-society').removeClass('active-society');
        $('#cluster').remove();
        
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
            log('  creating cluster nav element.');
            
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
            
            var elem = $('<li id="cluster"><a href="javascript:Tags.selectCluster(' + temp_format_value(this.clusterId) + ', ' + temp_format_value(this.sectorId) + ', null);">' + clusterName + '</a></li>');
            log('<li id="cluster"><a href="javascript:Tags.selectCluster(' + temp_format_value(this.clusterId) + ', ' + temp_format_value(this.sectorId) + ', null);">' + clusterName + '</a></li>');
            
            if (this.sectorId) {
                $('#sector-list-item-' + this.sectorId).append(elem);
            } else {
                $('#sector-list-item-all').append(elem);
            }
            
            if (!this.node || this.node.id != this.clusterId) {
                // Repeat this function until the node info is loaded, so we can show the cluster name.
                setTimeout(
                    function() {
                        Tags.updateHighlightedNode();
                    },
                    300
                );
            }
            
        } else if (this.page == this.PAGE_SOCIETY_CLUSTER) {
            
            log('  this.clusterId: ' + this.clusterId);
            
            // Highlight the selected society
            $('#society-list-item-' + this.societyId + ' a').addClass('active-society');
            var tabs = $('#left-column-container').data('nootabs');
			tabs.setTab('societies-tab');
			$('#tag-galaxy').addClass('tag-galaxy-viewing');
            
            // Highlight the selected cluster.
            // Create the cluster nav element.
            log('  creating cluster nav element.');
            
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
            
            var elem = $('<li id="cluster"><a href="javascript:Tags.selectCluster(' + temp_format_value(this.clusterId) + ', null, ' + temp_format_value(this.societyId) + ');">' + clusterName + '</a></li>');
            log('<li id="cluster"><a href="javascript:Tags.selectCluster(' + temp_format_value(this.clusterId) + ', null, ' + temp_format_value(this.societyId) + ');">' + clusterName + '</a></li>');
            
            if (this.societyId) {
                $('#society-list-item-' + this.societyId).append(elem);
            } else {
                $('#society-list-item-all').append(elem);
            }
            
            if (!this.node || this.node.id != this.clusterId) {
                // Repeat this function until the node info is loaded, so we can show the cluster name.
                setTimeout(
                    function() {
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
            $('#societies-tab').scrollTo($('#society-list-item-' + this.societyId), {offset: {top:-6, left:0}});
            $('#tag-galaxy').addClass('tag-galaxy-viewing');
        } else {
            // No node selected
        }
    },
    
    selectCluster: function(clusterId, sectorId, societyId) {
        var tags = this;
        log("selectCluster()");
        log("  clusterId: " + clusterId);
        log("  sectorId: " + sectorId);
        log("  societyId: " + societyId);
        
        if (sectorId != null) {
            this.page = this.PAGE_SECTOR_CLUSTER;
        } else if (societyId != null) {
            this.page = this.PAGE_SOCIETY_CLUSTER;
        }
        
        this.clusterId = clusterId;
        this.sectorId = sectorId;
        this.societyId = societyId;
        
        this.node = null;
        this.nodeType = 'tag_cluster';
        this.updateChangedNode();
        
        var tagWindow = $("#tags");
        tagWindow.empty();
        tagWindow.html("<h1 id=\"wait\">Please wait...</h1>");
        
        var filterStr = implode(',', this.getFilters());
        
        // Hide any flyvoers so they don't persist when the node is gone.
        Flyover.hide();
        
        $.get(
            '/ajax/textui_nodes',
            {
                node_id: clusterId,
                sector_id: sectorId,
                society_id: societyId,
                filterValues: filterStr,
                sort: this.getSort()
            },
            function(data) {
                Tags.onLoadClusters(data);
            }
        );
        
        // Get the cluster node's info (to display the name).
        log('Loading node info');
        $.getJSON(
            '/ajax/node',
            {
                nodeId: clusterId,
            },
            function(data) {
                log('Got node info');
                log('  tags.clusterId: ' + tags.clusterId);
                log('  data.id: ' + data.id);
                if (data.id == tags.clusterId) {
                    log('node id matches.');
                    tags.node = data;
                }
            }
        );
    },
    
    onLoadClusters: function(data) {
        log('onLoadClusters()');
        var tagWindow = $("#tags");
        tagWindow.html(data);
		this.updateZoom();
    },
    
    getTagById: function(id) {
        for (var i=0; i<this.tags.length; i++) {
            if (this.tags[i].id == id) {
                return this.tags[i];
            }
        }
        return null;
    },
    
    selectTag: function(id, tabName) {
        //console.log("selectTag()");
        //console.log("id: " + id);
        this.updateChangedNode();
        
        //$('.tag').removeClass('activeTag');
        
        // Highlight the current tag
        var tagBlock = $('#tag-' + id);
        //tagBlock.addClass('activeTag');
        
        // Hide the flyover so it doesn't overlap with the lightbox
        Flyover.hide();

        // Show resource results in a lightbox
        // if there was no tab name given, use the default tab
        if (tabName == undefined) {
            Lightbox.show('/ajax/tag_content/' + id + '/textui', {
                verticalCenter: false,
                customClass: 'resources',
                onShowCallback: function() {
                    $('#tag-name').effect("highlight", {}, 2000);
                    $(document).trigger('onShowLightboxTab');
                }
            });
        } else {
            Lightbox.show('/ajax/tag_content/' + id + '/textui', {
                verticalCenter: false,
                customClass: 'resources',
                onShowCallback: function() {
                    Tags.onSelectTag(tabName);
                    $('#tag-name').effect("highlight", {}, 2000);
                    $(document).trigger('onShowLightboxTab');
                }
            });
        }
    },
    
    onSelectTag: function(tabName) {
        var tabs = $('#resource-tabs').data('nootabs');
        tabs.setTab(tabName);
    },
    
    getFilters: function() {
        var result = [];
        var filters = $('.filter');
        for (var i=0; i<filters.length; i++) {
            //console.log("i: " + i);
            //console.log("filters[i].id: " + filters[i].id);
            //console.log("filters[i].value: " + filters[i].value);
            //console.log("filters[i].checked: " + filters[i].checked);
            if (filters[i].checked)
                result.push(filters[i].value);
        }
        return result;
    },
    
    getSort: function() {
        return sortDropDown.val();
    },
    
    updateSwitchLink: function() {
		// NOTE: Roamer is disabled. No need for switch link.
        //if (this.sectorId != null) {
        //    if (this.nodeType == 'sector') {
        //        $('#switch-link').attr('href', '/roamer#/sector/' + this.sectorId);
        //    } else {
        //        alert('ERROR in updateSwitchLink(): Unrecognized nodeType "' + this.nodeType + '"');
        //    }
        //} else {
        //    $('#switch-link').attr('href', '/roamer');
        //}
    },
    
    updateSort: function() {
        if (this.page == this.PAGE_SECTOR) {
            this.selectSector(this.sectorId);
        } else if (this.page == this.PAGE_SECTOR_CLUSTER) {
            this.selectCluster(this.clusterId, this.sectorId, null);
        } else if (this.page == this.PAGE_SOCIETY_CLUSTER) {
            this.selectCluster(this.clusterId, null, this.societyId);
        } else if (this.page == this.PAGE_SOCIETY) {
            this.selectSociety(this.societyId);
        } else {
            alert('Tags.updateSort(): Error, page (' + this.page + ') must be "sector", "tag_cluster", or "society".');
        }
    },
    
    clearSectorSociety: function(setHash) {
        this.page = null;
        this.sectorId = "all";
        this.clusterId = null;
        this.societyId = null;
        $('#tags-live-search').val('');
        this.updateResults();
        $('#tag-galaxy').removeClass('tag-galaxy-viewing');
        $("#tags-live-search").focus();
    },
    
    setDefaultZoomValues: function(){
        this.defaultVertMargin = Math.round(parseInt($('#tags .node').css('margin-top')));
        this.defaultHorizMargin = Math.round(parseInt($('#tags .node').css('margin-left')));
        this.defaultTextSize = Math.round(parseInt($('#tags .node').css('font-size')));
        
		// In IE, the CSS 'height' is 'auto'.
		var height = parseInt($('#tags .node').css('height'));
		if (isNaN(height)) {
			this.defaultHeight = $('#tags .node').attr('offsetHeight');
		} else {
			this.defaultHeight = Math.round(height);
		}
		
        this.defaultPadding = Math.round(parseInt($('#tags .node').css('padding-top')));
    },
    
    updateZoom: function() {
        var tags = this;

        // Save the initial sizes to use later.
        if (typeof this.defaultVertMargin == 'undefined'){
            this.setDefaultZoomValues();
        }
    
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
            
            this._showWaitScreenOver(function() {
                // This function is called after the waiting screen is shown.
                
                // Scales down the effect of this zoom.
                function scaleZoom(zoom, scale) {
                    if (zoom >= 100) {
                        return (zoom - 100) * scale + 100;
                    } else {
                        return zoom;
                    }
                }
                
                $('#tags .node').css('margin-top', (tags.defaultVertMargin * zoom / 100) + 'px');
                $('#tags .node').css('margin-bottom', (tags.defaultVertMargin * zoom / 100) + 'px');
                $('#tags .node').css('margin-left', (tags.defaultHorizMargin * zoom / 100) + 'px');
                $('#tags .node').css('margin-right', (tags.defaultHorizMargin * zoom / 100) + 'px');
                $('#tags .node').css('font-size', (tags.defaultTextSize * zoom / 100) + 'px');
                $('#tags .node').css('height', (tags.defaultHeight * zoom / 100) + 'px');
                $('#tags .node').css('padding-top', (tags.defaultPadding * scaleZoom(zoom, 2) / 100) + 'px');
                $('#tags .node').css('padding-bottom', (tags.defaultPadding * scaleZoom(zoom, 2) / 100) + 'px');
                $('#tags .node').css('padding-left', (tags.defaultPadding * scaleZoom(zoom, 3) / 100) + 'px');
                $('#tags .node').css('padding-right', (tags.defaultPadding * scaleZoom(zoom, 3) / 100) + 'px');
                
                tags._hideWaitScreenOver();
            });
            
        }
        
        this.oldZoom = zoom;
        
		//log('~resizeNodes()');
	}
    
};
