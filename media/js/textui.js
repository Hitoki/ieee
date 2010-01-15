
function getNode(parent, name) {
    var nodes = parent.getElementsByTagName(name);
    if (nodes.length != 1) {
        alert("getNode(" + parent + ", " + name + "): found " + nodes.length + " nodes.");
        return null;
    }
    return nodes[0];
}

var Tags = {
    
    nodeId: null,
    societyId: null,
    nodeType: null,
    selectedClusterId: null,
    node: null,
    onLoadSectorCallback: null,
    helpScreenElem: null,
    tagSortOverlayElem: null,
    oldHash: null,
    
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
            var sector_matches = hash.match(/^\/sector\/(\d+)$/);
            
            // Matches "#/society/123"
            var society_matches = hash.match(/^\/society\/(\d+)$/);
            
            if (hash == '') {
                // Home page
                this.showHelp(false);
                
            } else if (sector_matches) {
                // Sector
                var sectorId = parseInt(sector_matches[1]);
                if (this.nodeId != sectorId) {
                    this.selectSector(sectorId, null, false);
                }
            
            } else if (society_matches) {
                // Society
                var societyId = parseInt(society_matches[1]);
                if (this.societyId != societyId) {
                    this.selectSociety(societyId, null, false);
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
        this.updateDisabledFilters();
        this.updateHighlightedNode();
        this.updateSwitchLink();
        
        if (this.nodeId == null) {
            if (!this.tagSortOverlayElem) {
                this.tagSortOverlayElem = $('<div id="tag-sort-overlay"></div>').appendTo('body');
                this.tagSortOverlayElem.bgiframe();
                
                var pos = $('#tag-sort').position();
                this.tagSortOverlayElem.css('top', pos.top);
                this.tagSortOverlayElem.css('left', pos.left);
                this.tagSortOverlayElem.css('width', $('#tag-sort').attr('offsetWidth'));
                this.tagSortOverlayElem.css('height', $('#tag-sort').attr('offsetHeight'));
                
                Flyover.attach(this.tagSortOverlayElem, {
                    'content': 'Please start by selecting an Industry Section or IEEE Society',
                    'position': 'bottom'
                    
                });
            }
            $('#tag-sort').attr('disabled', 'disabled');
        } else {
            if (this.tagSortOverlayElem) {
                Flyover.detach(this.tagSortOverlayElem);
                this.tagSortOverlayElem.remove();
                this.tagSortOverlayElem = null;
            }
            $('#tag-sort').attr('disabled', '');
            Flyover.detach($('#tag-sort'));
        }
    },
    
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
    
    selectSector: function(id, onload, setHash) {
        //log('selectSector()');
        //log('  id: ' + id);
        
        if (id) {
            this.nodeId = id;
            this.societyId = null;
            this.nodeType = 'sector';
        }
        
        if (setHash == undefined) {
            setHash = true;
        }
        
        if (setHash) {
            //log('setting hash to "' + '/sector/' + this.nodeId + '"');
            $.historyLoad('/sector/' + this.nodeId);
        }
        
        if (this.nodeId != null) {
            
            this.hideHelp();
            
            // Hide the content lightbox if it's visible.
            Lightbox.hide();
            
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
            
            var filterStr = implode(',', this.getFilters());
            
            if (onload) {
                this.onLoadSectorCallback = onload;
            }
            
            // Hide any flyvoers so they don't persist when the node is gone.
            Flyover.hide();
            
            $.ajax({
                url: '/ajax/textui_nodes',
                data: {
                    sector_id: this.nodeId,
                    sort: this.getSort()
                },
                success: function(data) {
                    Tags.onLoadResults(data);
                }
            });
        }
    },
    
    selectSociety: function(societyId, onload, setHash) {
        //log('selectSector()');
        //log('  societyId: ' + societyId);
        
        if (societyId) {
            this.societyId = societyId;
            this.nodeId = null;
            this.nodeType = null;
        }
        
        if (setHash == undefined) {
            setHash = true;
        }
        
        if (setHash) {
            //log('setting hash to "' + '/sector/' + this.nodeId + '"');
            $.historyLoad('/society/' + this.societyId);
        }
        
        if (this.societyId != null) {
            
            this.hideHelp();
            
            // Hide the content lightbox if it's visible.
            Lightbox.hide();
            
            // Update the switch interfaces link
            //this.updateChangedNode();
        
            var tagWindow = $("#tags");
            
            tagWindow.empty();
            tagWindow.html(
                '<div id="loading" class="please-wait">'
                + '<h1>Please wait...</h1>'
                + '<img src="' + MEDIA_URL + '/images/ajax-loader-bar.gif" />'
                + '</div>'
            );
            
            var filterStr = implode(',', this.getFilters());
            
            if (onload) {
                this.onLoadSectorCallback = onload;
            }
            
            // Hide any flyvoers so they don't persist when the node is gone.
            Flyover.hide();
            
            $.ajax({
                url: '/ajax/textui_nodes',
                data: {
                    society_id: this.societyId,
                    sort: this.getSort()
                },
                success: function(data) {
                    Tags.onLoadResults(data);
                }
            });
            
            this.updateHighlightedNode();
        }
    },
    
    showSearchResults: function(search_for) {
        this.search_for = search_for;
        this.societyId = null;
        this.nodeId = null;
        this.nodeType = null;
        
        this.updateHighlightedNode();
        
        log('searching for "' + this.search_for + '"');
        $.ajax({
            url: '/ajax/textui_nodes',
            data: {
                search_for: this.search_for
            },
            success: function(data) {
                Tags.onLoadResults(data);
            }
        });
    },
    
    onLoadResults: function(data) {
        var tagWindow = $("#tags");
        tagWindow.html(data);
    },
    
    updateHighlightedNode: function() {
        //log('updateHighlightedNode()');
        
        // Remove any active sectors
        $('#sectors a.active-sector').removeClass('active-sector');
        $('#societies a.active-society').removeClass('active-society');
        
        // If a cluster was highlighted, remove it
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
            /*
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
            */
        }
        
        //log('this.nodeId: ' + this.nodeId);
        //log('this.societyId: ' + this.societyId);
        //log('this.nodeType: ' + this.nodeType);
        
        if (this.nodeId != null && this.nodeType == 'sector') {
            // Highlight the selected sector
            $('#sector-list-item-' + this.nodeId + ' a').addClass('active-sector');
            var tabs = $('#left-column-container').data('nootabs');
			tabs.setTab('sectors-tab');
        } else if (this.nodeId != null && this.nodeType == 'tag_cluster') {
            // Highlight the selected cluster
            //$('#cluster-list-item-' + this.nodeId + ' a').addClass('active-sector');
            if (this.node) {
                $('#sector-list-item-' + this.node.sectorId + ' a').addClass('active-sector');
            }
            var tabs = $('#left-column-container').data('nootabs');
			tabs.setTab('sectors-tab');
        } else if (this.societyId != null) {
            // Highlight the selected society
            $('#society-list-item-' + this.societyId + ' a').addClass('active-society');
            var tabs = $('#left-column-container').data('nootabs');
            tabs.setTab('societies-tab');
        } else if (this.nodeId == null) {
            // No node selected
            
        } else {
            alert('ERROR: Unknown this.nodeType "' + this.nodeType + '"');
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
            Lightbox.show('/ajax/tag_content?tagId=' + id + '&ui=textui', {
                verticalCenter: false,
                customClass: 'resources'
            });
        } else {
            Lightbox.show('/ajax/tag_content?tagId=' + id + '&ui=textui', {
               verticalCenter: false,
               customClass: 'resources',
               onShowCallback: function() {
                   Tags.onSelectTag(tabName);
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
        return $('#tag-sort')[0].options[$('#tag-sort')[0].selectedIndex].value;
    },
    
    updateSwitchLink: function() {
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
    
    showHelp: function(setHash) {
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
    }
    
};
