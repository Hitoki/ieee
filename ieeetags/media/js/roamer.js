
function getConstellationRoamer() {
    if (document.all)
        return document.all('constellation-roamer-object');
    else
        return document.getElementById('constellation-roamer-embed');
}

var Roamer = {
    flash: null,
    id: null,
    filters: {},
    oldHash: null,
    
    init: function() {
        var roamer = this;
        
        //log("Roamer.init()");
        this.flash = getConstellationRoamer();
        //log("this.flash: " + this.flash);
        
        var filters = $(".filter");
        for (var i=0; i<filters.length; i++) {
            this.filter(filters[i].id, filters[i].checked);
        }
        
        roamer.onChangeHash(encodeURIComponent(window.location.hash));
        
        // Need to manually call this when page is loaded if hash is empty.
        if (window.location.hash == '' || window.location.hash == '#') {
            this.onChangeHash(window.location.hash);
        }
        
        this.onChange();
    },

    onChangeHash: function(hash) {
        if (this.oldHash != hash) {
            
            // Matches "#/sector/123"
            var sector_matches = hash.match(/^\/sector\/(\d+)$/);
            // Matches "#/tag/123"
            var tag_matches = hash.match(/^\/tag\/(\d+)$/);
            
            if (hash == '') {
                // Home page
                this.setNode(1, false);
                
            } else if (sector_matches) {
                // Sector
                var sectorId = parseInt(sector_matches[1]);
                if (this.id != sectorId) {
                    log('  setting id to ' + sectorId);
                    this.setNode(sectorId, false);
                }
            
            } else if (tag_matches) {
                // Tag
                var tagId = parseInt(tag_matches[1]);
                if (this.id != tagId) {
                    log('  setting id to ' + tagId);
                    this.setNode(tagId, false);
                }
            
            } else {
                // Catch all for bad hashes... especially "#tag-login-tab" leftover from login redirect...
                this.showHelp(false);
                
            }
            
            this.oldHash = hash;
        }
    },
    
    getSectorLink: function(id) {
        var sectors = $('#sectors a');
        for (var i=0; i<sectors.length; i++) {
            var data = $(sectors[i]).metadata();
            //log("* data.id: " + data.id);
            if (data.id == id) {
                return $(sectors[i]);
            }
        }
        return null;
    },
    
    // Highlight the current sector (if there is one)
    highlightSector: function() {
        // Remove the old highlight (if any)
        $('#sectors a').removeClass('active-sector');
        if (this.nodeInfo.type == 'sector') {
            // Selected node is a sector, highlight it
            var link = this.getSectorLink(this.nodeInfo.id);
            link.addClass('active-sector');
        } else if (this.nodeInfo.type == 'tag_cluster') {
            // Selected node is a sector, highlight it
            var sectorId = this.nodeInfo.parents[0].id;
            var link = this.getSectorLink(sectorId);
            link.addClass('active-sector');
        }
    },
    
    // Get the selected node from roamer
    getNode: function(id) {
        id = this.flash.getSelectedNodeID();
        return id;
    },
    
    setNode: function(id, setHash) {
        //log("setNode()");
        //log("  id: " + id);
        //log("  setHash: " + setHash);
        //log("  this.flash.getSelectedNodeID(): " + this.flash.getSelectedNodeID());
        
        if (setHash == undefined) {
            setHash = true;
        }
        
        // Hide the content lightbox if it's visible.
        Lightbox.hide();
        
        this.flash.setSelectedNodeID(id);
        this.id = id;
        this.nodeInfo = null;
        this.getNodeInfo(setHash);
        this.loadContent();
        // TODO:
        //this.updateSector();
        this.updateSwitchLink();
    },
    
    getNodeInfo: function(setHash) {
        //log('getNodeInfo()');
        var results = null;
        // Get the info synchronously (save results in "results" var)
        $.ajax({
            async: false,
            success: function(data) {
                results = data;
            },
            data: {
                'nodeId': this.id
            },
            dataType: 'json',
            type: 'GET',
            url: 'ajax/node'
        });
        
        //log('  this.id: ' + this.id);
        //log('  results.id: ' + results.id);
        // Check if another node was selected after making the above ajax request
        if (this.id == results.id) {
            this.nodeInfo = results;
            this.highlightSector();
        }
        
        if (setHash) {
            // Update the hash...
            if (this.nodeInfo.type == 'sector') {
                //log('setting sector hash');
                window.location.hash = encodeURIComponent('/sector/' + this.nodeinfo.id);
            } else if (this.nodeInfo.type == 'tag') {
                //log('setting tag hash');
                window.location.hash = encodeURIComponent('/tag/' + this.nodeinfo.id);
            } else if (this.nodeInfo.type == 'root') {
                //log('setting root hash');
                window.location.hash = '';
            } else {
                ajax_report_error('ERROR in getNodeInfo(): unknown nodeInfo.type: ' + this.nodeInfo.type);
                return;
            }
        }
        
        //log('~getNodeInfo()');
    },
    
    // Called by roamer whenever the selected node changes
    onChange: function() {
        //log('onChange()');
        var id = this.flash.getSelectedNodeID();
        if (id != this.id) {
            this.id = id;
            this.nodeInfo = null;
            this.getNodeInfo(true);
            this.updateSwitchLink();
            this.loadContent();
        }
    },
    
    loadContent: function() {
        //log("loadContent()");
        //log("  this.id: " + this.id);
        //log("  this.nodeInfo: " + this.nodeInfo);
        if (this.nodeinfo) {
            //log("  this.nodeInfo.id: " + this.nodeInfo.id);
            //log("  this.nodeInfo.name: " + this.nodeInfo.name);
            //log("  this.nodeInfo.type: " + this.nodeInfo.type);
        }
        
        if (this.nodeInfo && this.nodeInfo.type == 'tag') {
            // Selected a tag, show the resources link bar (update name & count, flash green)
            if (this.nodeInfo.num_resources > 0) {
                $('#no-resources').hide();
                $('#resources-explanation-text').hide();
                $('#resources-link').show();
                // NOTE: jQuery always makes this <a> into 'display:inline', but we want 'display:block'
                $('#resources-link').css('display', 'block');
                
                $('.resources-tag-name').html(htmlentities(this.nodeInfo.name));
                $('#resources-count').html(htmlentities(this.nodeInfo.num_resources));
                
                // Adapt the label to show "Resources" or "Resource" appropriately
                if (this.nodeInfo.num_resources > 1)
                    $('#resources-plural').html('s');
                else
                    $('#resources-plural').html('');
                
                $('#resources-link').css('backgroundColor', 'green');
                $('#resources-link').animate(
                    {
                        'backgroundColor': '#006699'
                    },
                    1000
                );
                $('#resources-link').hover(
                    function(){
                        $(this).css('background-color', 'orange');
                    },
                    function(){
                        $(this).css('background-color', '#006699');
                    }
                );
            } else {
                $('#no-resources').show();
                $('#resources-explanation-text').hide();
                $('#resources-link').hide();
                $('.resources-tag-name').html(htmlentities(this.nodeInfo.name));
            }
            
            
        } else {
            // Not a tag, hide the resources link bar (show "clic
            $('#resources-explanation-text').show();
            $('#resources-link').hide();
            $('#no-resources').hide();
        }
        //log("~loadContent()");
    },
    
    filter: function(filterName, state) {
        //log("filter()");
        this.filters[filterName] = state;
        var filters = [];
        for (var i in this.filters) {
            //log("this.filters["+i+"]: " + this.filters[i]);
            if (this.filters[i])
                filters.push(i);
        }
        
        var filterStr = filters.join(" || ");
        //log("filterStr: " + filterStr);
        if (filterStr == '')
            filterStr = 'none';
        
        this.flash.setFilter(filterStr);
    },
    
    updateSwitchLink: function() {
        //log('updateSwitchLink()');
        //log('this.id: ' + this.id);
        if (this.nodeInfo.type == 'sector' || this.nodeInfo.type == 'tag_cluster') {
            // Enable the switch link for sectors and clusters
            $('#switch-link').attr('href', '/textui#/sector/' + this.id);
            Flyover.detach($('#switch-link'));
            
        } else if (this.nodeInfo.type == 'tag') {
            // Disable the switch link for tags
            $('#switch-link').attr('href', 'javascript:void(0);');
            Flyover.attach($('#switch-link'));
            
        } else if (this.nodeInfo.type == 'root') {
            // Root switch link (blank hash)
            $('#switch-link').attr('href', '/textui');
            Flyover.detach($('#switch-link'));
            
        } else {
            ajax_report_error('ERROR in updateSwitchLink(): unknown nodeInfo.type "' + this.nodeInfo.type + '"');
            return;
        }
        //log('~updateSwitchLink()');
    },
    
    showResourceResultsLightbox: function() {
        Lightbox.show('/ajax/tag_content/' + this.nodeInfo.id + '/roamer', {
            verticalCenter: false,
            customClass: 'resources',
            onShowCallback: function() {
                    $(document).trigger('onShowLightboxTab');
                }
        });
    }
};

/* Constellation Roamer hooks */

function constellationRoamer_onLoaded() {
    //log("constellationRoamer_onLoaded()");
    Roamer.init();
    //Roamer.onChange();
}

function constellationRoamer_onChange(nodeID) {
    //log("constellationRoamer_onChange()");
    Roamer.onChange();
}

function constellationRoamer_onClick(nodeID) {
    //log("constellationRoamer_onClick()");
}

function constellationRoamer_onDoubleClick(nodeID) {
    //log("constellationRoamer_onDoubleClick()");
}

function constellationRoamer_onEdgeClick(edgeID) {
    //log("constellationRoamer_onEdgeClick()");
}

function constellationRoamer_onEdgeDoubleClick(edgeID) {
    //log("constellationRoamer_onEdgeDoubleClick()");
}

function constellationRoamer_onError(str) {
    //log("constellation error: " + str);
    ajax_report_error("constellation error: " + str);
    return;
}

////////////////////////////////////////


