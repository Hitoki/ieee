
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
    nodeType: null,
    selectedClusterId: null,
    node: null,
    onLoadSectorCallback: null,
    helpScreenElem: null,
    
    init: function() {
    },
    
    selectSector: function(id, onload) {
        //log('selectSector()');
        //log('  id: ' + id);
        
        this.hideHelp();
        
        if (id) {
            this.nodeId = id;
            this.nodeType = 'sector';
        }
        
        // Update the switch interfaces link
        this.updateSwitchLink();
            
        this.updateHighlightedNode();
        
        var tagWindow = $("#tags");
        
        tagWindow.empty();
        tagWindow.html(
            '<div id="loading" class="please-wait">'
            + '<h1>Please wait...</h1>'
            + '<img src="' + MEDIA_URL + '/images/ajax-loader-bar.gif" />'
            + '</div>'
        );
        
        var filterStr = implode(',', this.getFilters());
        
        if (onload)
            this.onLoadSectorCallback = onload;
        
        // Hide any flyvoers so they don't persist when the node is gone.
        Flyover.hide();
        
        $.getJSON('/ajax/nodes_json', {nodeId:this.nodeId, filterValues:filterStr, sort:this.getSort()}, function(data) { Tags.onLoadSector(data); });
    },
    
    onLoadSector: function(data) {
        this.node = data.node.sector;
        /*
        //console.log("onLoadSector()");
        var results = [];
        for (var i=0; i<data.length; i++) {
            var node = data[i];
            if (node.type == 'tag') {
                results.push(node);
            }
        }
        this.renderTags(results);
        */
        this.renderTags(data);
    },
    
    updateHighlightedNode: function() {
        // Remove any active sectors
        $('#sectors a.active-sector').removeClass('active-sector');
        
        
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
        
        // Highlight the selected sector
        if (this.nodeType == 'sector') {
            $('#sector-list-item-' + this.nodeId + ' a').addClass('active-sector');
        } else if (this.nodeType == 'tag_cluster') {
            //$('#cluster-list-item-' + this.nodeId + ' a').addClass('active-sector');
            $('#sector-list-item-' + this.node.sectorId + ' a').addClass('active-sector');
        } else {
            alert('ERROR: Unknown this.nodeType "' + this.nodeType + '"');
        }
    },
    
    selectCluster: function(id) {
        //log("selectCluster()");
        //log("  id: " + id);
        
        this.nodeId = id;
        this.nodeType = 'tag_cluster';
        
        var tagWindow = $("#tags");
        tagWindow.empty();
        tagWindow.html("<h1 id=\"wait\">Please wait...</h1>");
        
        var filterStr = implode(',', this.getFilters());
        
        // Update the switch interfaces link
        this.updateSwitchLink();
        
        // Hide any flyvoers so they don't persist when the node is gone.
        Flyover.hide();
        
        $.getJSON(
            '/ajax/nodes_json',
            {
                nodeId:id,
                filterValues:filterStr,
                sort:this.getSort()
            },
            function(data) {
                Tags.onLoadClusters(data);
            }
        );
    },
    
    onLoadClusters: function(data) {
        //log('onLoadClusters()');
        //log('  data.node.sector.id: ' + data.node.sector.id);
        
        this.node = data.node;
        this.node.sectorId = data.node.sector.id;
        
        this.updateHighlightedNode();
        
        this.renderTags(data);
    },
    
    _renderBlock: function(type, tagWindow, node, sectorId) {
        var str;
        str = "";
        str += "<div id=\"tag-" + node.id + "\" class=\"node " + type + "\">";
        // NOTE: Table is here to prevent the label & color blocks from wrapping onto separate lines
        str += "  <table>";
        str += "    <tr>";
        str += "      <td>";
        
        // Truncate long node names.  The flyover will show the full node name.
        var label = node.label;
        var MAX_TAG_LENGTH = 30;
        if (label.length > MAX_TAG_LENGTH) {
            label = label.substr(0, MAX_TAG_LENGTH) + '...';
        }
        
        if (type == 'tag') {
            str += "        <a href=\"javascript:Tags.selectTag(" + node.id + ");\" class=\"" + node.level + "\">" + htmlentities(label) + "</a> ";
        } else if (type == 'tag_cluster') {
            str += "        <img src=\"/media/images/icon_cluster_sm.png\" />";
            str += "        <a href=\"javascript:Tags.selectCluster(" + node.id + ");\" class=\"" + node.level + "\">" + htmlentities(label) + "</a> ";
        } else {
            alert('Unknown node type "' + type + '" for node "' + node.label + '"');
        }
        str += "      </td>";
        str += "      <td>";
        str += "        <div class=\"node-block-container\">";
        str += "          <div class=\"block-top " + node.sectorLevel + "\">&nbsp;</div>";
        str += "          <div class=\"block-bottom " + node.relatedTagLevel + "\">&nbsp;</div>";
        str += "        </div>";
        str += "      </td>";
        str += "    </tr>";
        str += "  </table>";
        str += "</div>";
        
        var div = $(str);
        div.appendTo(tagWindow);
        div.data('tagId', node.id);
        div.data('sectorId', sectorId);
        
        if (type == 'tag') {
            // Show the tag flyover
            div.hover(
                function() {
                    Flyover.show(
                        this,
                        {
                            url: '/ajax/tooltip/'+$(this).data('tagId')+'/'+$(this).data('sectorId'),
                            position: 'auto',
                            customClass: 'textui-node',
                            hideDelay: 100
                        }
                    );
                },
                function() {
                    Flyover.onMouseOut();
                }
            );
        } else if (type == 'tag_cluster') {
            // Show the cluster flyover
            div.hover(
                function() {
                    Flyover.show(
                        this,
                        {
                            url: '/ajax/tooltip/'+$(this).data('tagId')+'/'+$(this).data('sectorId'),
                            position: 'auto',
                            hideDelay: 100
                        }
                    );
                },
                function() {
                    Flyover.onMouseOut();
                }
            );
        } else {
            alert('ERROR: Unknown type "' + type + '"');
        }
    },
    
    renderTags: function(data) {
        
        // Save the tags for the title later
        //this.tags = tags;
        this.data = data;
        
        var tagWindow = $("#tags");
        tagWindow.empty();
        
        //$('<div>Sector: ' + this.nodeId + '</div>').appendTo(tagWindow);
        
        //console.log("tags.length: " + tags.length);
        
        if (data.node.type == 'sector') {
            
            // Sector title
            //var title = $('<h2>' + htmlentities(data.node.sector.label) + ' sector</h2>').appendTo(tagWindow);
            
            // Show "no clusters" warning if applicable
            if (this.getSort() == 'clusters_first_alpha') {
                
                var numClusters = 0;
                for (var i=0; i<data.child_nodes.length; i++) {
                    if (data.child_nodes[i].type == 'tag_cluster') {
                        numClusters++;
                    }
                }
                
                if (numClusters == 0) {
                    // Show the "no clusters" warning
                    var noClustersWarning = $('<p class="no-clusters-warning">There are no clusters in this sector for the selected filters.</p>').appendTo(tagWindow);
                }
            }
            
        } else if (data.node.type == 'tag_cluster') {
            var sectorLink = $('<a href="javascript:Tags.selectSector(' + data.node.sector.id + ');" class="back-link"></a>').appendTo(tagWindow);
            sectorLink.html('<img src="' + MEDIA_URL + '/images/arrow2-up-small.png" /> Up to the "' + htmlentities(data.node.sector.label) + '" sector');
            $('<br/>').appendTo(tagWindow);
            
            // Cluster title
            var title = $('<h2>' + htmlentities(data.node.label) + ' cluster</h2>').appendTo(tagWindow);
            
            
        } else {
            alert('Unknown data.node.type "' + data.node.type + '"')
        }
        
        // Show tags
        for (var i=0; i<data.child_nodes.length; i++) {
            this._renderBlock(data.child_nodes[i].type, tagWindow, data.child_nodes[i], this.nodeId);
        }
        
        if (this.onLoadSectorCallback) {
            this.onLoadSectorCallback();
            this.onLoadSectorCallback = null;
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
        
        //$('.tag').removeClass('activeTag');
        
        // Highlight the current tag
        var tagBlock = $('#tag-' + id);
        //tagBlock.addClass('activeTag');
        
        // Hide the flyover so it doesn't overlap with the lightbox
        Flyover.hide();
        
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
        //console.log('updateSwitchLink()');
        //console.log('this.nodeId: ' + this.nodeId);
        $('#switch-link')[0].href = '/roamer?nodeId=' + this.nodeId;
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
    
    showHelp: function() {
        this.hideHelp();
        
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
   
