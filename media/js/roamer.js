
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
    
    init: function() {
        //log("Roamer.init()");
        this.flash = getConstellationRoamer();
        //log("this.flash: " + this.flash);
        
        var filters = $(".filter");
        for (var i=0; i<filters.length; i++) {
            this.filter(filters[i].id, filters[i].checked);
        }
        
        this.onChange();
    },
    
    /*
    updateSector: function() {
        //log("updateSector()");
        var roamer = this;
        this.id = this.flash.getSelectedNodeID();
        this.nodeInfo = null;
        $.getJSON('/ajax/node', {nodeId:this.id}, function(data){roamer.updateSector2(data);} );
        //log("~updateSector()");
    },
    */
    
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
    
    highlightSector: function(id) {
        //log('highlightSector()');
        $('#sectors a').removeClass('active-sector');
        var link = this.getSectorLink(id);
        link.addClass('active-sector');
        //log('~highlightSector()');
    },
    
    /*
    updateSector2: function(data) {
        //log("updateSector2()");
        //log('data', data);
        //log('data.type', data.type);
        //log('data.parent', data.parent);
        //if (data.parent)
        //    //log('data.parent.id', data.parent.id);
        if (data.type == 'sector') {
            this.highlightSector(data.id);
        } else if (data.type == 'tag') {
            // TODO: Fix this for "parents" instead of "parent":
            //this.highlightSector(data.parent.id);
        }
        //log("~updateSector2()");
    },
    */
    
    // Get the selected node from roamer
    getNode: function(id) {
        id = this.flash.getSelectedNodeID();
        return id;
    },
    
    setNode: function(id) {
        //log("setNode()");
        //log("  id: " + id);
        //log("  this.flash.getSelectedNodeID(): " + this.flash.getSelectedNodeID());
        
        this.flash.setSelectedNodeID(id);
        this.id = id;
        this.nodeInfo = null;
        this.loadContent();
        // TODO:
        //this.updateSector();
        this.updateSwitchLink();
    },
    
    getNodeInfo: function() {
        //log('getNodeInfo()');
        var results = null;
        function copyResults(data) {
            results = data;
        }
        // Get the info synchronously
        $.ajax({
            async: false,
            success: copyResults,
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
            //log('  this.nodeInfo: ' + this.nodeInfo);
        }
        
        //log('~getNodeInfo()');
    },
    
    // Called by roamer whenever the selected node changes
    onChange: function() {
        //log("onChange()");
        var id = this.flash.getSelectedNodeID();
        if (id != this.id) {
            this.id = id;
            this.nodeInfo = null;
            this.getNodeInfo();
            this.updateSwitchLink();
            this.loadContent();
            // TODO:
            //this.updateSector();
        }
        //log("~onChange()");
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
            $('#resources-explanation-text').hide();
            $('#resources-link').show();
            $('#resources-tag-name').html(htmlentities(this.nodeInfo.name));
            $('#resources-count').html(htmlentities(this.nodeInfo.num_resources));
            $('#resources-link').css('backgroundColor', 'green');
            $('#resources-link').animate(
                {
                    'backgroundColor': '#006699'
                },
                1000
            );
            
        } else {
            // Not a tag, hide the resources link bar (show "clic
            $('#resources-explanation-text').show();
            $('#resources-link').hide();
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
        $('#switch-link')[0].href = '/textui?nodeId=' + this.id;
        //log('~updateSwitchLink()');
    },
    
    showResourceResultsLightbox: function() {
        Lightbox.show('/ajax/tag_content?tagId=' + this.nodeInfo.id, {
            verticalCenter: false,
            customClass: 'resources'
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
    alert("constellation error: " + str);
}

////////////////////////////////////////


