
// Gets the position of an element relative to a given parent element
function getPositionRelativeTo(node, parent) {
	node = $(node);
	parent = $(parent);
	var left = 0
	var top = 0;
	while (node[0] != parent[0] && node[0].nodeName != 'BODY') {
		left += node.position().left;
		top += node.position().top;
		node = node.offsetParent();
	}
	return {
		left: left,
		top: top
	}
}

function ExpandSeries(rowElem) {
    //log('ExpandSeries()');
	var expandSeries = this;
    
	this.isExpanded = false;
	
    this.rowElem = $(rowElem);
    this.conferenceId = this.rowElem.metadata().id;
    
    // TODO: This prevents series with only one conference (the current one) from having JS errors... need to fix later.
    if ($('.sub-conference-' + this.conferenceId).length == 0) {
        this.rowElem.hide();
        return;
    }
    
    // This finds the parent DIV where we should append all images.
    this.containerElem = this.rowElem.parent().parent().parent().parent();
    
    this.imgTopElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_top.png" class="curly-brace"/>');
    this.imgTopElem.appendTo(this.containerElem)
    
    this.imgBottomElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_bottom.png" class="curly-brace"/>');
    this.imgBottomElem.appendTo(this.containerElem);
    
    this.imgMiddleElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_middle.png" class="curly-brace"/>');
    this.imgMiddleElem.appendTo(this.containerElem);
    
    this.imgUpperElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_repeat.png" class="curly-brace"/>');
    this.imgUpperElem.appendTo(this.containerElem);
    
    this.imgLowerElem = $('<img src="' + MEDIA_URL + 'images/curly_brace_repeat.png" class="curly-brace"/>');
    this.imgLowerElem.appendTo(this.containerElem);
	
	this.middleDivElem = $('<div class="curly-brace-mid-div"></div>');
    this.middleDivElem.appendTo(this.containerElem);
	
	this.expandLinkElem = $('<a href=""></a>');
	this.expandLinkElem.appendTo(this.middleDivElem);
	this.expandLinkElem.click(function() {
		expandSeries.toggle();
		return false;
	});
	
	this.selectAllLinkElem = $('<a href=""><img src="' + MEDIA_URL + '/images/checkbox_on.png" /> Select All</a>');
	this.selectAllLinkElem.appendTo(this.middleDivElem);
	this.selectAllLinkElem.click(function() {
		expandSeries.selectAll();
		return false;
	});
	
	this.selectNoneLinkElem = $('<a href=""><img src="' + MEDIA_URL + '/images/checkbox.png" /> Select None</a>');
	this.selectNoneLinkElem.appendTo(this.middleDivElem);
	this.selectNoneLinkElem.click(function() {
		expandSeries.selectNone();
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
			$('.sub-conference-' + this.conferenceId).each(function() {
                if (firstSubConference == null) {
                    firstSubConference = $(this);
                }
                lastSubConference = $(this);
			});
			
			var cellPos = getPositionRelativeTo(firstSubConference, this.containerElem);
			topPoint = cellPos.top;
			
			cellPos = getPositionRelativeTo(lastSubConference, this.containerElem);
			bottomPoint = cellPos.top + lastSubConference[0].offsetHeight;
			
			leftPoint = parseInt(cellPos.left - this.imgTopElem[0].offsetWidth) - 1;
		} else {
			// Work from the expand link's row
			var cellPos = getPositionRelativeTo(this.rowElem, this.containerElem);
			topPoint = cellPos.top;
			bottomPoint = cellPos.top + this.rowElem[0].offsetHeight;
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
	if (doToggle == undefined || doToggle) {
		this.isExpanded = !this.isExpanded;
	}
	var isExpanded = this.isExpanded;
    
    // Toggle all sub-conferences
	$('.sub-conference-' + this.conferenceId).each(function() {
        if (isExpanded) {
            $(this).show();
        } else {
            $(this).hide();
        }
	});
	
	if (this.isExpanded) {
        this.rowElem.hide();
		this.expandLinkElem.html('<img src="' + MEDIA_URL + '/images/minusbox.png" /> Collapse Series');
        this.selectAllLinkElem.show();
        this.selectNoneLinkElem.show();
	} else {
        this.rowElem.show();
		this.expandLinkElem.html('<img src="' + MEDIA_URL + '/images/plusbox.png" /> Expand Series');
        this.selectAllLinkElem.hide();
        this.selectNoneLinkElem.hide();
	}
	
	this.reposition();
}

ExpandSeries.prototype.selectAll = function() {
	$('.sub-conference-' + this.conferenceId + ' .select-resources').each(function() {
        this.checked = true;
	});
    updateBatchEditResourcesButtons();
}

ExpandSeries.prototype.selectNone = function() {
	$('.sub-conference-' + this.conferenceId + ' .select-resources').each(function() {
        this.checked = false;
	});
    updateBatchEditResourcesButtons();
}
