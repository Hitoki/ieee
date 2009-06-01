
function getNode(parent, name) {
    var nodes = parent.getElementsByTagName(name);
    if (nodes.length != 1) {
        alert("getNode(" + parent + ", " + name + "): found " + nodes.length + " nodes.");
        return null;
    }
    return nodes[0];
}

var Tags = {
    
    sectorId: null,
    onLoadSector: null,
    
    init: function() {
    },
    
    findSectorLink: function(id) {
        //console.log("findSectorLink()");
        var links = $('#sectors a');
        
        for (var i=0; i<links.length; i++) {
            var results = links[i].href.match(/[0-9]+/);
            if (results.length != 1) {
                alert("findSectorLink(): error, found " + results.length + " numbers, need 1");
                return null;
            }
            //console.log("results[0]: " + results[0]);
            if (results[0] == id)
                return links[i];
        }
        //console.log("not found");
        return null;
    },
    
    selectSector: function(id, onload) {
        //console.log('selectSector()');
        //console.log('id: ' + id);
        
        if (id)
            this.sectorId = id;
        
        // Update the switch interfaces link
        this.updateSwitchLink();
            
        // Remove any active sectors
        var links = $('#sectors a');
        for (var i=0; i<links.length; i++) {
            $(links[i]).removeClass('active-sector');
        }
        
        var sectorLink = this.findSectorLink(this.sectorId);
        $(sectorLink).addClass('active-sector');
        
        var tagWindow = $("#tags");
        
        tagWindow.empty();
        tagWindow.html("<h1 id=\"wait\">Please wait...</h1>");
        
        var filters = this.getFilters();
        var filterStr = implode(',', filters);
        
        if (onload)
            this.onLoadSector = onload;
        
        $.getJSON('/ajax/nodes_json', {sectorId:this.sectorId, filterValues:filterStr, sort:this.getSort()}, Tags.onLoadNodes);
    },
    
    onLoadNodes: function(data) {
        //console.log("onLoadNodes()");
        var results = [];
        for (var i=0; i<data.length; i++) {
            var node = data[i];
            if (node.type == 'tag') {
                results.push(node);
            }
        }
        Tags.renderTags(results);
    },
    
    renderTags: function(tags) {
        
        // Save the tags for the title later
        this.tags = tags;
        
        var tagWindow = $("#tags");
        tagWindow.empty();
        
        //$('<div>Sector: ' + this.sectorId + '</div>').appendTo(tagWindow);
        
        //console.log("tags.length: " + tags.length);
        
        $('#tag-galaxy h2').html('Tag Galaxy (' + tags.length + ')'); 
        
        var str;
        for (var i=0; i<tags.length; i++) {
            var tag = tags[i];
            str = "";
            str += "<div id=\"tag-" + tag.id + "\" class=\"tag\">";
            str += "  <a href=\"javascript:Tags.selectTag(" + tag.id + ");\" class=\"" + tag.level + "\">" + tag.label + "</a> ";
            str += "  <div class=\"tag-block-container\">";
            str += "    <div class=\"block-top " + tag.sectorLevel + "\">a</div>";
            str += "    <div class=\"block-bottom " + tag.relatedTagLevel + "\">a</div>";
            str += "  </div>";
            str += "</div>";
            
            var div = $(str);
            div.appendTo(tagWindow);
            div.data('tagId', tag.id);
            div.data('sectorId', this.sectorId);
            
            div.hover(
                function() {
                    Tooltip.show({elem:this, url:'/ajax/tooltip?tag_id='+$(this).data('tagId')+'&sector_id='+$(this).data('sectorId'), loadBeforeShowing:true});
                },
                function() {
                    Tooltip.onMouseOut();
                }
            );
        }
        
        if (this.onLoadSector) {
            this.onLoadSector();
            this.onLoadSector = null;
        }
    },
    
    getTagById: function(id) {
        for (var i=0; i<this.tags.length; i++) {
            if (this.tags[i].id == id) {
                return this.tags[i];
            }
        }
        return null;
    },
    
    selectTag: function(id) {
        //console.log("selectTag()");
        //console.log("id: " + id);
        
        // Update the switch interfaces link
        this.updateSwitchLink();
        
        $('.tag').removeClass('activeTag');
        
        // Highlight the current tag
        var tagBlock = $('#tag-' + id);
        tagBlock.addClass('activeTag');
        
        // Show resource results in a lightbox
        Lightbox.show('/ajax/tag_content?tagId=' + id, {
            verticalCenter: false,
            customClass: 'resources'
        });
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
        console.log('updateSwitchLink()');
        console.log('this.sectorId: ' + this.sectorId);
        $('#switch-link')[0].href = '/roamer?nodeId=' + this.sectorId;
    }
    
};
   
