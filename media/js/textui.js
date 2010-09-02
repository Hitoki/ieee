
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
    
    $("#tags-live-search").focus();
    
    function hideHelpBox() {
        var windowHeight = $(window).height();
        var navTabsHeight = $('#galaxy-tabs .nootabs-menu').eq(0).height();
        
        $('#tag-help-box').hide();
        $('div#sectors-tab, div#societies-tab').css('height', windowHeight - 326 - navTabsHeight);
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
    });
    
});

var Tags = {
    
    PAGE_SECTOR: 'sector',
    PAGE_SOCIETY: 'society',
    PAGE_HELP: 'help',
    PAGE_HOME: 'home',
    
    // The current page (sector/cluster, society, help, search, etc)
    page: null,
    isSearching: false,
    
    nodeId: null,
    societyId: null,
    nodeType: null,
    //selectedClusterId: null,
    node: null,
    helpScreenElem: null,
    tagSortOverlayElem: null,
    oldHash: null,
    oldZoom: null,
    
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
                this.showHelp(false);
                
            } else if (sector_matches) {
                // Sector
                var sectorId = sector_matches[1];
                if (sectorId !== "all") {
                    sectorId = parseInt(sectorId);
                }
                if (this.nodeId != sectorId) {
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
                this.showHelp(false);
                
            }
            
            this.oldHash = hash;
        }
    },
    
    // This should be called any time the selected node has changed
    updateChangedNode: function() {
        //this.updateDisabledFilters();
        this.updateHighlightedNode();
        this.updateSwitchLink();
        
        if (this.page == this.PAGE_SECTOR || this.page == this.PAGE_SOCIETY) {
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
		//log(' this.nodeId: ' + this.node);
		if (this.nodeId == null) {
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
        this.hideHome();
        this.hideHelp();
        
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
    
    selectSector: function(nodeId, setHash) {
        //log('selectSector()');
        //log('  nodeId: ' + nodeId);
        
        this.page = this.PAGE_SECTOR;
        
        this.nodeId = nodeId;
        this.societyId = null;
        this.nodeType = 'sector';
        
        if (setHash == undefined) {
            setHash = true;
        }
        
        if (setHash) {
            //log('setting hash to "' + '/sector/' + this.nodeId + '"');
            $.historyLoad('/sector/' + this.nodeId);
        }
        
        this.updateResults();
    },
    
    selectSociety: function(societyId, setHash) {
        //log('selectSociety()');
        //log('  societyId: ' + societyId);
        
        this.page = this.PAGE_SOCIETY
        
        this.societyId = societyId;
        this.nodeId = null;
        this.nodeType = null;
        
        if (setHash == undefined) {
            setHash = true;
        }
        
        if (setHash) {
            //log('setting hash to "' + '/sector/' + this.nodeId + '"');
            $.historyLoad('/society/' + this.societyId);
        }
        
        this.updateResults();
    },
    
    updateSort: function() {
        if (this.page == this.PAGE_SECTOR) {
            this.selectSector(this.nodeId);
        } else if (this.page == this.PAGE_SOCIETY) {
            this.selectSociety(this.societyId);
        } else {
            alert('Tags.updateSort(): Error, page (' + this.page + ') must be "sector" or "society".');
        }
    },
    
    showSearchResults: function(search_for, showSearchResultsCallback) {
        log('showSearchResults()');
        
        this.isSearching = true;
        
        this.updateHighlightedNode();
        
        if (this.page == this.PAGE_HOME) {
            this.page = this.PAGE_HELP;
        }
        
        this._showWaitScreen();
        
        log('  searching for "' + search_for + '"');
        
        this.updateResults(showSearchResultsCallback);
        /*
        var data = {
            search_for: search_for
        };
        if (this.page == this.PAGE_SOCIETY) {
            log('  was society, adding to data');
            data.society_id = this.societyId;
        } else if (this.page == this.PAGE_SECTOR) {
            log('  was sector, adding to data');
            data.sector_id = this.nodeId;
        } else if (this.page == this.PAGE_HELP) {
            log('  was help, doing nothing');
            // Do nothing
        } else {
            alert('Tags.showSearchResults(): Error, unknown page ' + this.page);
            return;
        }
        
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
        */
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
        
        if (this.nodeId != null) {
            // Load the sector
            $.ajax({
                url: '/ajax/textui_nodes',
                data: {
                    sector_id: this.nodeId,
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
                sector_id: this.nodeId
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
            this.showHelp();
            
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
        //log('updateHighlightedNode()');
        
        // Remove any active sectors
        $('#sectors a.active-sector').removeClass('active-sector');
        $('#societies a.active-society').removeClass('active-society');
        
        // If a cluster was highlighted, remove it
        /*
        if (this.selectedClusterId != null && this.selectedClusterId != this.nodeId) {
            // Remove all clusters, since they're no longer selected
            var listItem = $('.cluster-list-item');
            $('.cluster-list-item').fadeOut('slow', function() {
                // Cluster list item is done fading out, remove it from the page
                listItem.remove();
                listItem = null;
            });
            this.selectedClusterId = null;
        }
        
        // If a cluster was just selected, show & highlight it
        if (this.nodeType == 'tag_cluster' && this.selectedClusterId == null) {
            NOTE: This is disabled for now, just show the sector
            
            var sectorListItem = $('#sector-list-item-' + this.node.sectorId);
            
            var clusterListItem = $('<li id="cluster-list-item-' + this.nodeId + '" class="cluster-list-item"></li>');
            clusterListItem.hide();
            sectorListItem.after(clusterListItem);
            clusterListItem.fadeIn('slow');
            
            var link = $('<a></a>').appendTo(clusterListItem);
            link.text(this.node.label);
            link.attr('href', 'javascript:Tags.selectCluster(' + this.nodeId + ');');
            
            this.selectedClusterId = this.nodeId;
        }
        */
        
        if (this.page == this.PAGE_SECTOR) {
            // Highlight the selected sector
            $('#sector-list-item-' + this.nodeId + ' a').addClass('active-sector');
            var tabs = $('#left-column-container').data('nootabs');
			tabs.setTab('sectors-tab');
			$('#tag-galaxy').addClass('tag-galaxy-viewing');
            
        /*
        } else if (this.nodeId != null && this.nodeType == 'tag_cluster') {
            // Highlight the selected cluster
            //$('#cluster-list-item-' + this.nodeId + ' a').addClass('active-sector');
            if (this.node) {
                $('#sector-list-item-' + this.node.sectorId + ' a').addClass('active-sector');
            }
            var tabs = $('#left-column-container').data('nootabs');
			tabs.setTab('sectors-tab');
        */
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
    
    //selectCluster: function(id) {
    //    //log("selectCluster()");
    //    //log("  id: " + id);
    //    
    //    this.nodeId = id;
    //    this.societyId = null;
    //    this.nodeType = 'tag_cluster';
    //    
    //    var tagWindow = $("#tags");
    //    tagWindow.empty();
    //    tagWindow.html("<h1 id=\"wait\">Please wait...</h1>");
    //    
    //    var filterStr = implode(',', this.getFilters());
    //    
    //    this.updateChangedNode();
    //    
    //    // Hide any flyvoers so they don't persist when the node is gone.
    //    Flyover.hide();
    //    
    //    $.getJSON(
    //        '/ajax/textui_nodes',
    //        {
    //            nodeId:id,
    //            filterValues:filterStr,
    //            sort:this.getSort()
    //        },
    //        function(data) {
    //            Tags.onLoadClusters(data);
    //        }
    //    );
    //},
    //
    //onLoadClusters: function(data) {
    //    //log('onLoadClusters()');
    //    //log('  data.node.sector.id: ' + data.node.sector.id);
    //    
    //    this.node = data.node;
    //    this.node.sectorId = data.node.sector.id;
    //    
    //    this.updateChangedNode();
    //    
    //    this.renderTags(data);
    //},
    
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
		
		// Roamer is disabled. No need for swith link.
		return;
		
        if (this.nodeId != null) {
            if (this.nodeType == 'sector') {
                $('#switch-link').attr('href', '/roamer#/sector/' + this.nodeId);
            } else {
                alert('ERROR in updateSwitchLink(): Unrecognized nodeType "' + this.nodeType + '"');
            }
        } else {
            $('#switch-link').attr('href', '/roamer');
        }
    },
    
    refresh: function() {
		if (this.nodeType == 'sector') {
            this.selectSector(this.nodeId);
        } else if (this.nodeType == 'tag_cluster') {
            this.selectCluster(this.nodeId);
        } else {
            alert('Textui.refresh(): ERROR: unrecognized nodeType "' + this.nodeType + '"');
        }
    },
    
    clearSectorSociety: function(setHash) {
        this.nodeId = "all";
        this.societyId = null;
        $('#tags-live-search').val('');
        this.updateResults();
        $('#tag-galaxy').removeClass('tag-galaxy-viewing');
        $("#tags-live-search").focus();
    },
    
    showHome: function() {
        this.page = this.PAGE_HOME;
		
        // Unselect any node
		this.nodeId = null;
		this.societyId = null;

        this.updateChangedNode();
        
        var tagsElem = $('#tags');
        tagsElem.empty();
        
        this.homeOldPaddingLeft = $('.alt-box-pad').css('padding-left');
        this.homeOldPaddingRight = $('.alt-box-pad').css('padding-right');
        this.homeOldPaddingTop = $('.alt-box-pad').css('padding-top');
        this.homeOldPaddingBottom = $('.alt-box-pad').css('padding-bottom');
        $('.alt-box-pad').css('padding', '0px');
        
        this.homeScreenElem = $('<div class="textui-home"></div>').appendTo(tagsElem);
        this.homeScreenElem.load(TEXTUI_HOME_URL);
        
    },
    
    hideHome: function() {
        if (this.homeScreenElem) {
            this.homeScreenElem.remove();
            this.homeScreenElem = null;
            
            $('.alt-box-pad').css('padding-left', this.homeOldPaddingLeft);
            $('.alt-box-pad').css('padding-right', this.homeOldPaddingRight);
            $('.alt-box-pad').css('padding-top', this.homeOldPaddingTop);
            $('.alt-box-pad').css('padding-bottom', this.homeOldPaddingBottom);
        }
    },
    
    showHelp: function(setHash) {
        this.page = this.PAGE_HELP;
        
        if (setHash == undefined) {
            setHash = true;
        }
        
        if (setHash) {
            //log('setting hash to ""');
            $.historyLoad('');
        }
        
        this.hideHelp();
		
		// Unselect any node
		this.nodeId = null;
		this.societyId = null;
		this.nodeType = null;
		this.node = null;

        this.updateChangedNode();
        
        var tagsElem = $('#tags');
        tagsElem.empty();
        
        this.helpOldPaddingLeft = $('.alt-box-pad').css('padding-left');
        this.helpOldPaddingRight = $('.alt-box-pad').css('padding-right');
        this.helpOldPaddingTop = $('.alt-box-pad').css('padding-top');
        this.helpOldPaddingBottom = $('.alt-box-pad').css('padding-bottom');
        $('.alt-box-pad').css('padding', '0px');
        
        this.helpScreenElem = $('<div class="textui-help"></div>').appendTo(tagsElem);
        this.helpScreenElem.load(TEXTUI_HELP_URL);
    },
    
    hideHelp: function() {
        if (this.helpScreenElem) {
            this.helpScreenElem.remove();
            this.helpScreenElem = null;
            
            $('.alt-box-pad').css('padding-left', this.helpOldPaddingLeft);
            $('.alt-box-pad').css('padding-right', this.helpOldPaddingRight);
            $('.alt-box-pad').css('padding-top', this.helpOldPaddingTop);
            $('.alt-box-pad').css('padding-bottom', this.helpOldPaddingBottom);
        }
    },
	
	updateZoom: function() {
		//log('resizeNodes()');

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
            
            var defaultVertMargin = 13;
            var defaultHorizMargin = 7;
            var defaultTextSize = 14;
            var defaultHeight = 18;
            var defaultPadding = 3;
            
            // Scales down the effect of this zoom.
            function scaleZoom(zoom, scale) {
                if (zoom >= 100) {
                    return (zoom - 100) * scale + 100;
                } else {
                    return zoom;
                }
            }
            
            $('#tags .node').css('margin-top', (defaultVertMargin * zoom / 100) + 'px');
            $('#tags .node').css('margin-bottom', (defaultVertMargin * zoom / 100) + 'px');
            $('#tags .node').css('margin-left', (defaultHorizMargin * zoom / 100) + 'px');
            $('#tags .node').css('margin-right', (defaultHorizMargin * zoom / 100) + 'px');
            $('#tags .node').css('font-size', (defaultTextSize * zoom / 100) + 'px');
            $('#tags .node').css('height', (defaultHeight * zoom / 100) + 'px');
            $('#tags .node').css('padding-top', (defaultPadding * scaleZoom(zoom, 2) / 100) + 'px');
            $('#tags .node').css('padding-bottom', (defaultPadding * scaleZoom(zoom, 2) / 100) + 'px');
            $('#tags .node').css('padding-left', (defaultPadding * scaleZoom(zoom, 3) / 100) + 'px');
            $('#tags .node').css('padding-right', (defaultPadding * scaleZoom(zoom, 3) / 100) + 'px');
        }
        
        this.oldZoom = zoom;
        
		//log('~resizeNodes()');
	}
    
};
