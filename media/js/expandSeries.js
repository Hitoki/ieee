
function getPositionRelativeTo(node, parent) {
	//log('getPositionRelativeTo()');
	node = $(node);
	//log('  node[0].nodeName: ' + node[0].nodeName);
	parent = $(parent);
	//log('  parent[0].nodeName: ' + parent[0].nodeName);
	//log('  parent[0].id: ' + parent[0].id);
	var left = 0
	var top = 0;
	while (node[0] != parent[0] && node[0].nodeName != 'BODY') {
		//log('    node[0].nodeName: ' + node[0].nodeName);
		//log('    node[0].id: ' + node[0].id);
		//log('    adding ' + node.position().left + ', ' + node.position().top);
		left += node.position().left;
		top += node.position().top;
		//log('    left/top: ' + left + ', ' + top);
		node = node.offsetParent();
	}
	return {
		left: left,
		top: top
	}
}

function ExpandSeries(linkElem) {
    log('ExpandSeries()');
	var expandSeries = this;
	
	this.isExpanded = false;
	
    this.linkElem = $(linkElem);
	this.linkElem.click(function() {
		expandSeries.toggle();
		return false;
	});
    
	// The cell containing the expand link
    this.cellElem = this.linkElem.parent();
    
    // This finds the parent DIV where we should append all images.
    this.containerElem = this.linkElem.parent().parent().parent().parent().parent().parent();
    
    this.imgTopElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_top.png" class="curly-brace"/>');
    this.imgTopElem.appendTo(this.containerElem)
    
    this.imgBottomElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_bottom.png" class="curly-brace"/>');
    this.imgBottomElem.appendTo(this.containerElem);
    
    this.imgMiddleElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_middle.png" class="curly-brace"/>');
    this.imgMiddleElem.appendTo(this.containerElem);
    
    this.imgUpperElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_repeat.png" class="curly-brace-stretch"/>');
    this.imgUpperElem.appendTo(this.containerElem);
    
    this.imgLowerElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_repeat.png" class="curly-brace-stretch"/>');
    this.imgLowerElem.appendTo(this.containerElem);
	
	this.middleDivElem = $('<div class="curly-brace-mid-div"></div>');
    this.middleDivElem.appendTo(this.containerElem);
	
	this.middleLinkElem = $('<a href=""></a>');
	this.middleLinkElem.appendTo(this.middleDivElem);
	this.middleLinkElem.click(function() {
		expandSeries.toggle();
		return false;
	});
	
	this.toggle(false);
    this.reposition();
}

ExpandSeries.prototype.reposition = function() {
    var expandSeries = this;
    //log('reposition()');
    if (this.imgTopElem[0].offsetWidth == 0
		|| this.imgBottomElem[0].offsetWidth == 0
		|| this.imgMiddleElem[0].offsetWidth == 0
		|| this.imgUpperElem[0].offsetWidth == 0
		|| this.imgLowerElem[0].offsetWidth == 0) {
        // Keep looping until all images are loaded & visible.
        //log('  looping');
    } else {
        //log('  All images loaded.');
		
		var topPoint = 0;
		var bottomPoint = 0;
		var leftPoint = 0;
		
		if (this.isExpanded) {
			// Get the top & bottom sub-conference rows
			
			var firstSubConference = null;
			var lastSubConference = null;
			var id = this.linkElem.metadata().id;
			$('.sub-conference').each(function() {
				if ($(this).metadata().parentId == id) {
					if (firstSubConference == null) {
						firstSubConference = $(this);
					}
					lastSubConference = $(this);
				}
			});
			
			var cellPos = getPositionRelativeTo(firstSubConference, this.containerElem);
			topPoint = cellPos.top;
			
			cellPos = getPositionRelativeTo(lastSubConference, this.containerElem);
			bottomPoint = cellPos.top + lastSubConference[0].offsetHeight;
			
			leftPoint = parseInt(cellPos.left - this.imgTopElem[0].offsetWidth) - 1;
		} else {
			// Work from the expand link's row
			var cellPos = getPositionRelativeTo(this.cellElem, this.containerElem);
			topPoint = cellPos.top;
			bottomPoint = cellPos.top + this.cellElem[0].offsetHeight;
			leftPoint = parseInt(cellPos.left - this.imgTopElem[0].offsetWidth) - 1;
		}
		
		// Constants
		var topOffset = 8;
		var bottomOffset = -9;
		var middleOffset = -10;
		var middleDivOffsetLeft = 9;
		
		// Offset
		var middlePoint = (topPoint + bottomPoint) / 2;
		
		var top;
		var height;
		
		// Position the top
		top = parseInt(topPoint + topOffset - this.imgTopElem[0].offsetHeight);
		this.imgTopElem.css('left', leftPoint + 'px');
        this.imgTopElem.css('top', top + 'px');
		
		// Position the bottom
		top = parseInt(bottomPoint + bottomOffset);
        this.imgBottomElem.css('left', leftPoint + 'px');
        this.imgBottomElem.css('top', top + 'px');
		
		// Position the middle
		top = parseInt(middlePoint + middleOffset);
        this.imgMiddleElem.css('left', leftPoint + 'px');
        this.imgMiddleElem.css('top', top + 'px');
		
		// Position the middle DIV (text)
		top = parseInt(middlePoint + middleOffset);
		var left2 = parseInt(leftPoint - this.middleDivElem[0].offsetWidth + middleDivOffsetLeft);
        this.middleDivElem.css('left', left2 + 'px');
        this.middleDivElem.css('top', top + 'px');
		
		// Position the upper
		top = parseInt(topPoint + topOffset);
		height = parseInt((middlePoint + middleOffset) - (topPoint + topOffset) + 1);
		width = parseInt(this.imgMiddleElem[0].offsetWidth);
        this.imgUpperElem.css('left', leftPoint + 'px');
        this.imgUpperElem.css('top', top + 'px');
        this.imgUpperElem.css('height', height + 'px');
        this.imgUpperElem.css('width', width + 'px');
		
		// Position the lower
		top = parseInt(middlePoint + middleOffset + this.imgMiddleElem[0].offsetHeight);
		height = parseInt((bottomPoint + bottomOffset) - (middlePoint + middleOffset + this.imgMiddleElem[0].offsetHeight) + 1);
		width = parseInt(this.imgMiddleElem[0].offsetWidth);
        this.imgLowerElem.css('left', leftPoint + 'px');
        this.imgLowerElem.css('top', top + 'px');
        this.imgLowerElem.css('height', height + 'px');
        this.imgLowerElem.css('width', width + 'px');
    }
	
	setTimeout(function() {
		expandSeries.reposition();
	}, 100);
}

ExpandSeries.prototype.toggle = function(doToggle) {
	//log('toggle()');
	var id = this.linkElem.metadata().id;
	
	if (doToggle == undefined || doToggle) {
		this.isExpanded = !this.isExpanded;
	}
	var isExpanded = this.isExpanded;
	$('.sub-conference').each(function() {
		if ($(this).metadata().parentId == id) {
			if (isExpanded) {
				$(this).show();
			} else {
				$(this).hide();
			}
		}
	});
	
	if (this.isExpanded) {
		this.middleLinkElem.html('Collapse Series');
	} else {
		this.middleLinkElem.html('Expand Series');
	}
	
	this.reposition();
}
