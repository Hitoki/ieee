
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
        //console.log("Roamer.init()");
        this.flash = getConstellationRoamer();
        //console.log("this.flash: " + this.flash);
        
        var filters = $(".filter");
        for (var i=0; i<filters.length; i++) {
            this.filter(filters[i].id, filters[i].checked);
        }
        
        this.id = this.flash.getSelectedNodeID();
        this.loadContent();
        this.updateSector();
        this.updateSwitchLink();
    },
    
    updateSector: function() {
        //console.log("updateSector()");
        var roamer = this;
        this.id = this.flash.getSelectedNodeID();
        $.getJSON('/ajax/node', {nodeId:this.id}, function(data){roamer.updateSector2(data);} );
        //console.log("~updateSector()");
    },
    
    getSectorLink: function(id) {
        var sectors = $('#sectors a');
        for (var i=0; i<sectors.length; i++) {
            var data = $(sectors[i]).metadata();
            //console.log("* data.id: " + data.id);
            if (data.id == id) {
                return $(sectors[i]);
            }
        }
        return null;
    },
    
    highlightSector: function(id) {
        //console.log('highlightSector()');
        $('#sectors a').removeClass('active-sector');
        var link = this.getSectorLink(id);
        link.addClass('active-sector');
        //console.log('~highlightSector()');
    },
    
    updateSector2: function(data) {
        //console.log("updateSector2()");
        //log('data', data);
        //log('data.type', data.type);
        //log('data.parent', data.parent);
        //if (data.parent)
        //    log('data.parent.id', data.parent.id);
        if (data.type == 'sector') {
            this.highlightSector(data.id);
        } else if (data.type == 'tag') {
            this.highlightSector(data.parent.id);
        }
        //console.log("~updateSector2()");
    },
    
    getNode: function(id) {
        //console.log("getNode()");
        //console.log("this.flash: " + this.flash);
        //console.log("this.flash.getSelectedNodeID(): " + this.flash.getSelectedNodeID());
        id = this.flash.getSelectedNodeID();
        //console.log("id: " + id);
        return id;
    },
    
    setNode: function(id) {
        console.log("setNode()");
        console.log("  id: " + id);
        console.log("  this.flash.getSelectedNodeID(): " + this.flash.getSelectedNodeID());
        
        this.flash.setSelectedNodeID(id);
        this.id = id;
        this.loadContent();
        this.updateSector();
        this.updateSwitchLink();
    },
    
    onChange: function() {
        //console.log("onChange()");
        var id = this.flash.getSelectedNodeID();
        if (id != this.id) {
            this.id = id;
            this.updateSwitchLink();
            this.loadContent();
            this.updateSector();
        }
    },
    
    loadContent: function() {
        //console.log("loadContent()");
        //console.log("this.id: " + this.id);
        if (this.id)
            $("#content").load("/ajax/tag_content?tagId=" + this.id, null, function() { convertTabs(); });
        //console.log("~loadContent()");
    },
    
    filter: function(filterName, state) {
        //console.log("filter()");
        this.filters[filterName] = state;
        var filters = [];
        for (var i in this.filters) {
            //console.log("this.filters["+i+"]: " + this.filters[i]);
            if (this.filters[i])
                filters.push(i);
        }
        
        var filterStr = filters.join(" || ");
        //console.log("filterStr: " + filterStr);
        if (filterStr == '')
            filterStr = 'none';
        
        this.flash.setFilter(filterStr);
    },
    
    updateSwitchLink: function() {
        //console.log('updateSwitchLink()');
        //console.log('this.id: ' + this.id);
        $('#switch-link')[0].href = '/textui?nodeId=' + this.id;
        //console.log('~updateSwitchLink()');
    }
};

/* Constellation Roamer hooks */

function constellationRoamer_onLoaded() {
    //console.log("constellationRoamer_onLoaded()");
    Roamer.init();
    //Roamer.onChange();
}

function constellationRoamer_onChange(nodeID) {
    //console.log("constellationRoamer_onChange()");
    Roamer.onChange();
}

function constellationRoamer_onClick(nodeID) {
    //console.log("constellationRoamer_onClick()");
}

function constellationRoamer_onDoubleClick(nodeID) {
    //console.log("constellationRoamer_onDoubleClick()");
}

function constellationRoamer_onEdgeClick(edgeID) {
    //console.log("constellationRoamer_onEdgeClick()");
}

function constellationRoamer_onEdgeDoubleClick(edgeID) {
    //console.log("constellationRoamer_onEdgeDoubleClick()");
}

function constellationRoamer_onError(str) {
    //console.log("constellation error: " + str);
    alert("constellation error: " + str);
}

////////////////////////////////////////


